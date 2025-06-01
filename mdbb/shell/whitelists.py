from .. import Shell
from . import CommandResponse, logger

from core import DB
from plugins.cwcore import CWCore

from core.users import UserManager
from core.utils import get_mc_username
from core.templates.UserTemplate import WLStatus

import json

wl_changes = {
    "added": [],
    "removed": []
}

@Shell.command("wlsync", "Syncs the whitelist database with the server", "wlsync")
def wl_sync(ctx):
    logger.info("Running whitelist synchronization...")
    server_wl = json.loads(open("whitelist.json", "r", encoding="utf-8").read()) #{name: str, uuid: str}
    db_wl = DB.get("clockbot").users.find({"whitelist.status": WLStatus.APPROVED.value}) #user template objects
    
    #process server whitelist
    for u in server_wl:
        user = UserManager(minecraft=u["uuid"])
        if not user.is_valid():
            wl_changes["removed"].append({
                "uuid": u["uuid"],
                "name": get_mc_username(u["uuid"])
            })
            continue
       
        if user.get()["whitelist"]["status"] != WLStatus.APPROVED.value:
            wl_changes["added"].append({
                "uuid": u["uuid"],
                "name": get_mc_username(u["uuid"])
            })

    #process database whitelist
    server_wl_uuids = [u["uuid"] for u in server_wl]
    for user in db_wl:
        if user["minecraft"] not in server_wl_uuids and user["whitelist"]["status"] == WLStatus.APPROVED.value:
            wl_changes["added"].append({
                "uuid": user["minecraft"],
                "name": get_mc_username(user["minecraft"])
            })
    
    #display changes
    logger.info("Preview of whitelist changes:")
    logger.ok(f"[+] {len(wl_changes['added'])} users will be added to the whitelist")
    logger.error(f"[-] {len(wl_changes['removed'])} users will be removed from the whitelist")
    for u in wl_changes["added"]:
        logger.ok(f"+ {u['name']} ({u['uuid']})")
    for u in wl_changes["removed"]:
        logger.error(f"- {u['name']} ({u['uuid']})")
        
    if len(wl_changes["added"]) == 0 and len(wl_changes["removed"]) == 0:
        logger.info("No changes to the whitelist were detected")
        return CommandResponse("No changes to the whitelist were detected")
    
    return CommandResponse("To apply these changes, use the 'wlapply' command")

@Shell.command("wlapply", "Applies the pending whitelist changes", "wlapply")
def wl_apply(ctx):
    if len(wl_changes["added"]) == 0 and len(wl_changes["removed"]) == 0:
        return CommandResponse("No changes to apply, please run 'wlsync' first")
    
    #apply changes
    for u in wl_changes["added"]:
        CWCore.whitelist_add(u['uuid'])
        logger.ok(f"Added {u['name']} to the whitelist")
    
    for u in wl_changes["removed"]:
        CWCore.whitelist_remove(u['uuid'])
        logger.error(f"Removed {u['name']} from the whitelist")
    
    #clear changes
    wl_changes["added"].clear()
    wl_changes["removed"].clear()
    
    return CommandResponse("Whitelist changes applied successfully")