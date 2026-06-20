import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from services import member_service
import traceback

try:
    ids = member_service.get_all_member_ids()
    print("User IDs in DB:", ids)
    if ids:
        profile = member_service.get_member_profile_by_user_id(ids[0])
        print("Profile for first user:", profile)
except Exception as e:
    traceback.print_exc()
