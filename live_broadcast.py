from ItsAGramLive.ItsAGramLive import ItsAGramLive

live = ItsAGramLive()

broadcast_id = live.create_broadcast()

live.start_broadcast(broadcast_id)

live.end_broadcast(broadcast_id)

