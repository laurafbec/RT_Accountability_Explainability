from semantic_router import Route
from semantic_router.encoders import OpenAIEncoder
from semantic_router.layer import RouteLayer


class RouteQuery:
    navigation = Route(
        name="NavAnswers",
        utterances=[
            "How many goals did the robot successfully achieve?",
            "Where is goal number 2 located?",
            "Was any goal aborted or cancelled?",
            "Did the robot replan any trajectories?",
        ]
    )
    routes = [navigation]
    encoder = OpenAIEncoder()
    route_layer = RouteLayer(encoder=encoder, routes=routes)

