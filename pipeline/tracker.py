from uuid import uuid4


class VisitorTracker:
    """
    Simple MVP tracker.

    Later this can be replaced with:
    - ByteTrack
    - DeepSORT
    - Re-ID embeddings

    For now it creates stable visitor IDs
    for detected tracks.
    """

    def __init__(self):
        self.track_to_visitor = {}

    def get_visitor_id(self, track_id: int) -> str:
        if track_id not in self.track_to_visitor:
            self.track_to_visitor[track_id] = (
                f"VIS_{uuid4().hex[:8]}"
            )

        return self.track_to_visitor[track_id]