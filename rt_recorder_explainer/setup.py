import os
from glob import glob
from setuptools import setup

package_name = 'rt_recorder_explainer'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*')),
        (os.path.join('share', package_name, 'certs'), glob('certs/*.pem'))
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='laura',
    maintainer_email='laura@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'kafka_producer_node = rt_recorder_explainer.kafka_producer_node:main',
            'kafka_producer_srv = rt_recorder_explainer.kafka_producer_srv:main'
        ],
    },
)
