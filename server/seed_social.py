"""Seed badges, endorsements and message threads (some with unread messages for the demo)."""
from . import seed_data_social as demo
from .db import days_ago, now_iso


def seed_social(conn, ids, opportunity_ids) -> None:
    for handle, kind, label, verified in demo.BADGES:
        conn.execute("INSERT INTO badges (user_id, kind, label, verified_by_tutti, created) VALUES (?,?,?,?,?)",
                     (ids[handle], kind, label, int(verified), now_iso()))
    for musician, author, relationship, text in demo.ENDORSEMENTS:
        conn.execute("INSERT INTO endorsements (musician_id, author_id, relationship, text, created) VALUES (?,?,?,?,?)",
                     (ids[musician], ids[author], relationship, text, days_ago(5)))
    for first, second, opportunity_index, messages in demo.CONVERSATIONS:
        low, high = sorted((ids[first], ids[second]))
        audition_id = opportunity_ids[opportunity_index] if opportunity_index is not None else None
        cur = conn.execute("INSERT INTO conversations (user_low, user_high, audition_id, created) VALUES (?,?,?,?)",
                           (low, high, audition_id, days_ago(2)))
        for sender, text, hours_ago, read in messages:
            sent = days_ago(hours_ago / 24)
            conn.execute("INSERT INTO messages (conversation_id, sender_id, body, created, read_at) VALUES (?,?,?,?,?)",
                         (cur.lastrowid, ids[sender], text, sent, sent if read else None))
