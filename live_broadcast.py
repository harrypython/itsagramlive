from ItsALive.ItsALive import ItsALive

live = ItsALive()

broadcast_id = live.create_broadcast()

live.start_broadcast(broadcast_id)

live.end_broadcast(broadcast_id)

