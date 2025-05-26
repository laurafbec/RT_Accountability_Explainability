import os
import rclpy
from rclpy.node import Node
from rclpy.time import Time
from confluent_kafka import Producer
from std_srvs.srv import SetBool
from rcl_interfaces.msg import Log
from nav2_msgs.msg import BehaviorTreeLog
from geometry_msgs.msg import PoseWithCovarianceStamped, Twist
from action_msgs.msg import GoalStatusArray
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import Path
from rclpy.qos import QoSProfile, QoSDurabilityPolicy, QoSHistoryPolicy, QoSReliabilityPolicy

from ament_index_python.packages import get_package_share_directory
from uuid import uuid4
import yaml
import json
import math

from rclpy.logging import LoggingSeverity


# Mapping dictionary to convert numeric log levels to string representations
LOG_LEVEL_MAP = {
    10: "DEBUG",
    20: "INFO",
    30: "WARNING",
    40: "ERROR",
    50: "FATAL",
}

# Mapping Nav2 BT nodes' names into a description
NAV2_BT_MAP = {
    "ComputePathToPose": "plans a path to a target",
    "FollowPath": "tracks a specified path",
    "RateController": "throttles the tick rate",
    "NavigateWithReplanning": "replans the path in real-time",
    "NavigateRecovery": "recovers from issues"
}

# Mapping Nav2 BT nodes' status into a description
NAV2_BT_STATUS_MAP = {
    "IDLE": "is waiting to be executed",
    "RUNNING": "is running",
    "SUCCESS": "has succeeded",
    "FAILURE": "has failed"
}


class TamperProofBagRecorder(Node):

    DISTANCE_THRESHOLD = 1.2 #(20%)
    OBSTACLE_DISTANCE_THRESHOLD = 1.4 #1.4 m
    NGOALS = 3
    
    def __init__(self):
        super().__init__('kafka_producer_srv')

        self.rosout_qos = QoSProfile(
          durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
          reliability=QoSReliabilityPolicy.RELIABLE,
          history=QoSHistoryPolicy.KEEP_LAST,
          depth=1000)
        
        self.amcl_pose_qos = QoSProfile(
          durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
          reliability=QoSReliabilityPolicy.RELIABLE,
          history=QoSHistoryPolicy.KEEP_LAST,
          depth=5)
        
        self.navigate_to_pose_action = QoSProfile(
          durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
          reliability=QoSReliabilityPolicy.RELIABLE,
          history=QoSHistoryPolicy.KEEP_LAST,
          depth=5)

        self.scan_qos = QoSProfile(
          durability=QoSDurabilityPolicy.VOLATILE,
          reliability=QoSReliabilityPolicy.BEST_EFFORT,
          history=QoSHistoryPolicy.KEEP_LAST,
          depth=500)

        self.cmd_vel_qos = QoSProfile(
          durability=QoSDurabilityPolicy.VOLATILE,
          reliability=QoSReliabilityPolicy.RELIABLE,
          history=QoSHistoryPolicy.KEEP_LAST,
          depth=100)
        
         # Initialize variables
        self.previous_goal_id = None
        self.finished_goals = []
        self.n_goal = 0
        self.nav_status_log_message = "No navigation is running. "

        self.last_scan = ""
        self.previous_distance = float('inf')
        self.changed_route_log_message = "Planned path has not changed. "
      


        param_descriptors = [
            ('rosout', rclpy.Parameter.Type.INTEGER),
            ('behavior_tree_log', rclpy.Parameter.Type.INTEGER),
            ('amcl_pose', rclpy.Parameter.Type.INTEGER),
            ('navigate_to_pose/_action/status', rclpy.Parameter.Type.INTEGER),
            ('scan', rclpy.Parameter.Type.INTEGER),
            ('plan', rclpy.Parameter.Type.INTEGER),
            ('cmd_vel', rclpy.Parameter.Type.INTEGER)
            

        ]

        # Get parameters values
        self.declare_parameters(
            namespace='',
            parameters=param_descriptors
        )

        # Get parameters values
        param_names = [param[0] for param in param_descriptors]

        # Initialize an array to store parameter values
        parameter_values = {}

        # Iterate over parameter names to get and store parameter values
        for param_name in param_names:
            param_value = self.get_parameter(param_name).get_parameter_value().integer_value
            parameter_values[param_name] = param_value

        # Topics and QoS profiles definition
        self.topics_qos_profiles = {
            'rosout': (Log, 'rcl_interfaces/msg/Log', self.rosout_qos, parameter_values.get('rosout', 5)),
            'behavior_tree_log': (BehaviorTreeLog, 'nav2_msgs/msg/BehaviorTreeLog', None, parameter_values.get('behavior_tree_log', 15)),
            'amcl_pose': (PoseWithCovarianceStamped, 'geometry_msgs/msg/PoseWithCovarianceStamped', self.amcl_pose_qos, parameter_values.get('amcl_pose', 10)),
            'navigate_to_pose/_action/status': (GoalStatusArray, 'action_msgs/msg/GoalStatusArray', self.navigate_to_pose_action, parameter_values.get('navigate_to_pose/_action/status', 1)),
            'scan': (LaserScan, 'sensor_msgs/msg/LaserScan', self.scan_qos, parameter_values.get('scan', 50)),
            'plan': (Path, 'nav_msgs/msg/Path', None, parameter_values.get('plan', 5)),
            'cmd_vel': (Twist, 'geometry_msgs/msg/Twist', self.cmd_vel_qos, parameter_values.get('cmd_vel', 15))
        }

        # Messages processing functions
        self.extraction_functions = {
            "rosout": self.extract_rosout_info,
            #"behavior_tree_log": self.extract_behavior_tree_info,
            "amcl_pose": self.extract_amcl_pose_info,
            "navigate_to_pose/_action/status": self.extract_navigateToPose_action,
            'scan': self.extract_scan_action_info,
            'plan': self.extract_plan_info,
            'cmd_vel': self.extract_cmd_vel_info 
        }

        # Record var init
        self.record = False

        # Blockchain approach vars
        self.topic_messages_counters = {}

        # Service definition
        self.srv = self.create_service(SetBool, 'kafka_producer_srv', self.RtRecorder_callback)
    


    def RtRecorder_callback(self, request, response):
        
        default_qos = 10

        if request.data == True:
            # Subscription to /rosout topic
            self.load_kafka_config()

            # Topic's subscription
            for topic, (msg_type, type_string, qos_profile, bc_rate) in self.topics_qos_profiles.items():
                if qos_profile is None:
                    qos_profile = default_qos

                self.subscription = self.create_subscription(msg_type, topic, lambda msg, topic_name=topic, bc_rate=bc_rate: self.topic_callback(msg, topic_name, bc_rate), qos_profile)
            
            response.success = True
            response.message = 'Recording...'
            self.record = True

        if request.data == False:
            response.success = False
            response.message = 'Not recording...'
            self.record = False
        
        return response

    def load_kafka_config(self):
        # Get the absolute file path of the .pem files    
        self.CARoot_cert_file = os.path.join(get_package_share_directory('rt_recorder_explainer'), 'certs', 'CARoot.pem')
        self.producer_cert_file = os.path.join(get_package_share_directory('rt_recorder_explainer'), 'certs', 'producer.pem')
        self.producer_key_file = os.path.join(get_package_share_directory('rt_recorder_explainer'), 'certs', 'producer_key.pem')

        self.kafka_topic_name = "ROSMessagesTopic" 
        self.conf = {'bootstrap.servers': 'broker1:19093',
                'security.protocol': 'SSL',
                'ssl.ca.location': self.CARoot_cert_file,
                'ssl.certificate.location': self.producer_cert_file,
                'ssl.key.location': self.producer_key_file,
                #'debug':'all',
                'ssl.endpoint.identification.algorithm':'none'
            }


    def publish_to_kafka(self, json_string):
        producer = Producer(self.conf)
        producer.poll(0)
        # Producción de mensajes asíncrona con Kafka
        try:
            producer.produce(topic=self.kafka_topic_name, key=str(uuid4()), value=json_string.encode(), on_delivery=self.delivery_report)
            producer.flush()
        except Exception as ex:
            self.get_logger().error(f"Exception: {ex}")

    def delivery_report(self, errmsg, msg):
        if errmsg is not None:
            self.get_logger().error(f"Fallo en la entrega del mensaje: {msg.key()} : {errmsg}")
        #else:
        #    self.get_logger().info(f"Mensaje: {msg.key()} producido exitosamente en el Topic: {msg.topic()} en la Partición: [{msg.partition()}] en el offset {msg.offset()}")

        # Detener el nodo después de enviar los mensajes
        #self.get_logger().info("Mensajes enviados exitosamente")


    # Callbacks functions to pass the serialized message to the writer
    def topic_callback(self, msg, topic_name, bc_rate):    
        if self.record:
            try:
                if topic_name not in self.topic_messages_counters:
                  self.topic_messages_counters[topic_name] = 0

                self.topic_messages_counters[topic_name] += 1
                self.last_msg = msg

                extraction_function = self.extraction_functions.get(topic_name)
                if extraction_function:
                    extraction_function(topic_name,msg) 

            except RuntimeError:
                self.get_logger().error('{} topic has not been created yet! Call create_topic first.'.format(topic_name))

    # Process messages from /rosout topic
    def extract_rosout_info(self, topic_name, msg):
        current_time = self.get_clock().now()
        sec, nanosec = current_time.seconds_nanoseconds()

        log_data = {
            "topic_name": "rosout",
            "log_level": LOG_LEVEL_MAP.get(msg.level, "UNKNOWN"),
            "name": msg.name, 
            "message": msg.msg, 
            "file_location": msg.file,
            "function_name": msg.function, 
            "line_number": msg.line,
            "log_message": f"{sec}.{nanosec} Log level: {LOG_LEVEL_MAP.get(msg.level, 'UNKNOWN')} "
                       f"Message: {msg.msg} File location: {msg.file} Function name: {msg.function} Line number: {msg.line}"
        }

        self.publish_to_kafka(json.dumps(log_data, indent=4))

    # Process messages from /behavior_tree_log topic
    def extract_behavior_tree_info(self, topic_name, msg):
        event_logs = []
        node_status_counts = {}  # Diccionario clásico para contar eventos

        current_time = self.get_clock().now()
        sec, nanosec = current_time.seconds_nanoseconds()

        # Iterate over all event logs in the message
        for event in msg.event_log:
            node_name = event.node_name
            node_description = NAV2_BT_MAP.get(node_name, node_name)
            current_status = event.current_status
            current_status_description = NAV2_BT_STATUS_MAP.get(current_status, current_status)

            # Use a key combining node_name, description, and status to group events
            key = (node_name, node_description, current_status_description)
        
            # Contar las ocurrencias de cada nodo/estado
            if key in node_status_counts:
                node_status_counts[key] += 1
            else:
                node_status_counts[key] = 1

            # Agregar cada evento al log estructurado
            event_logs.append({
                "timestamp": {
                    "sec": event.timestamp.sec,
                    "nanosec": event.timestamp.nanosec
                },
                "node_name": node_name,
                "node_description": node_description,
                "current_status": current_status,
                "current_status_description": current_status_description
            })

        # Construcción del mensaje compacto del log
        log_message_parts = []
        for (node_name, description, status), count in node_status_counts.items():
            if count > 1:
                log_message_parts.append(f"{node_name} ({description}): {status} ({count} times)")
            else:
                log_message_parts.append(f"{node_name} ({description}): {status}")
    
        # Obtener el timestamp del primer evento
        if msg.event_log:
            timestamp = f"{sec}.{nanosec}"
            log_message = f"{timestamp} " + "; ".join(log_message_parts)
        else:
            log_message = "No events in message"

        # Crear y publicar log_data
        if event_logs:
            log_data = {
                "topic_name": topic_name,
                "events": event_logs,
                "log_message": log_message
            }
            self.publish_to_kafka(json.dumps(log_data, indent=4))



    # Process messages from /amcl_pose topic
    def extract_amcl_pose_info(self, topic_name, msg):
        # Extraer las coordenadas y orientaciones
        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y
        z = msg.pose.pose.orientation.z
        w = msg.pose.pose.orientation.w
        current_time = self.get_clock().now()
        sec, nanosec = current_time.seconds_nanoseconds()

        log_data = {
            "topic_name": "amcl_pose",
            "pose": {
                "position": {"x": x, "y": y},
                "orientation": {"z": z, "w": w}
            },
            "log_message": f"{sec}.{nanosec} Position: {x}, {y}. Orientation: {z}, {w}"
        }

        self.publish_to_kafka(json.dumps(log_data, indent=4))

     # Process messages from /cmd_vel topic
    def extract_cmd_vel_info(self, topic_name, msg):
        current_time = self.get_clock().now()
        sec, nanosec = current_time.seconds_nanoseconds()
        x = msg.linear.x
        y = msg.linear.y
        z = msg.angular.z

        log_data = {
            "topic_name": "cmd_vel",
            "linear": {"x": x, "y": y},
            "angular": {"z": z},
            "log_message": f"{sec}.{nanosec} Linear velocity: {x}, {y}. Angular velocity: {z}"
        }
        self.publish_to_kafka(json.dumps(log_data, indent=4))

    
    # Process messages from NavigateToPose action status
    def extract_navigateToPose_action(self, topic_name, msg):
        self.nav_status_log_message = ""
        current_time = self.get_clock().now()
        sec, nanosec = current_time.seconds_nanoseconds()

        for status in msg.status_list:
            current_goal_id = str(status.goal_info.goal_id)
        
            # When a new goal is started
            if current_goal_id != self.previous_goal_id and current_goal_id not in self.finished_goals:
                self.previous_distance = float('inf')
                self.previous_goal_id = current_goal_id
                self.n_goal += 1
                if (self.n_goal == 1):
                    self.get_logger().info('Starting navigation task.')
                self.nav_status_log_message = f"Navigation to the goal number {self.n_goal} has started."
        
            # If navigation status changes (e.g., in progress, succeeded, cancelled, aborted)
            if status.status in [2, 4, 5, 6] and current_goal_id not in self.finished_goals:
                status_dict = {
                    2: "is in progress",
                    4: "has succeeded",
                    5: "was cancelled",
                    6: "has been aborted"
                }
                self.nav_status_log_message = f"Navigation to the goal number {self.n_goal} {status_dict[status.status]}."
                # Mark the goal as finished if the status is final (succeeded, cancelled, aborted)
                if status.status in [4, 5, 6]:
                    self.finished_goals.append(current_goal_id)
                    if len(self.finished_goals) == TamperProofBagRecorder.NGOALS:
                        self.get_logger().info('Navigation task has been completed.')
    
        # If no message was generated, provide a default message
        if not self.nav_status_log_message:
            self.nav_status_log_message = "No navigation is running."
        
        # Create a dictionary with the log data
        log_data = {
            "topic_name": topic_name,
            "goal_id": current_goal_id,
            "goal_number": self.n_goal,
            "log_message": f"{sec}.{nanosec} {self.nav_status_log_message}"
        }

        self.publish_to_kafka(json.dumps(log_data, indent=4))


    # Get last laser scan message
    def extract_scan_action_info(self, topic_name, msg):
        self.last_scan = msg

    # Process messages from /plan topic. Used to detect a change in a planned trajectory
    def extract_plan_info(self, topic_name, msg):
        current_time = self.get_clock().now()
        sec, nanosec = current_time.seconds_nanoseconds()

        total_distance = 0
        
        self.changed_route_log_message = "Planned path has not changed."

        for i in range(len(msg.poses) -1):
            p1 = msg.poses[i].pose.position
            p2 = msg.poses[i+1].pose.position
            distance = math.sqrt((p2.x - p1.x)**2 + (p2.y - p1.y)**2 + (p2.z - p1.z)**2)
            total_distance += distance
        
        # Euclidean distance checkings to detect a change in the planned trajectory
        if total_distance > self.previous_distance * TamperProofBagRecorder.DISTANCE_THRESHOLD:
            self.changed_route_log_message = f"Planned path has changed when trying to achieve goal pose number {self.n_goal}"
            if min(self.last_scan.ranges) < TamperProofBagRecorder.OBSTACLE_DISTANCE_THRESHOLD:
                self.changed_route_log_message += " because there was an obstacle."
            else:
                self.changed_route_log_message += "."
            self.changed_route_log_message += f"The trajectory has been replanned in order to achieve the goal pose number {self.n_goal}."
            

        self.previous_distance = total_distance

        #if self.changed_route_log_message:
        #    self.get_logger().info(self.changed_route_log_message)

        # Create a dictionary with the log data
        log_data = {
            "topic_name": topic_name,
            "log_message": f"{sec}.{nanosec} {self.changed_route_log_message}"
        }

        self.publish_to_kafka(json.dumps(log_data, indent=4))

    
    
def main(args=None):
    rclpy.init(args=args)
    sbr = TamperProofBagRecorder()
    rclpy.spin(sbr)
    rclpy.shutdown()


if __name__ == '__main__':
    main()