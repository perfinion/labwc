#!/usr/bin/env python

import sys
sys.path.append("/home/jason/code/xfce/labwc/pybase")
import time

from pywayland.client import Display
from pyinterop.protocol.wayland import WlOutput, WlRegistry, WlSeat, WlShm

from pyinterop.protocol.ext_workspace_v1 import (
    ExtWorkspaceManagerV1,
    ExtWorkspaceGroupHandleV1,
    ExtWorkspaceHandleV1,
)

from pyinterop.protocol.ext_foreign_toplevel_list_v1 import (
    ExtForeignToplevelListV1,
    ExtForeignToplevelHandleV1,
)

from pyinterop.protocol.ext_foreign_toplevel_workspace_unstable_v1 import (
    ExtForeignToplevelWorkspaceHandleV1,
    ExtForeignToplevelWorkspaceManager,
)


class WorkspaceLister:
    """A Wayland client that lists workspaces and then exits."""

    def __init__(self):
        self.display = Display()
        self.display.connect()

        # --- State ("User Data") ---
        self.workspace_manager = None
        self.workspace_counter = 0
        self.workspace_groups = []
        self.workspace_handles = []
        self.workspace_names = []
        # A flag to signal when we are done and can exit the loop
        self.finished = False

        self.toplevel_list = None
        self.toplevel_counter = 0

        # Start by listening to the registry
        registry = self.display.get_registry()
        self._reg_dispatcher(registry, "global")
        self._reg_dispatcher(registry, "global_remove")

        # Initial roundtrip to get the globals
        self.display.dispatch(block=True)
        self.display.roundtrip()

        if not self.workspace_manager:
            print("Error: Compositor does not support ext_workspace_manager_v1.")
            self.display.disconnect()
            sys.exit(1)

    def _reg_dispatcher(self, proxy, event):
        name = proxy.interface.name
        if name.startswith("ext_"):
            name = name[len("ext_"):]
        if name.endswith("_v1"):
            name = name[:-len("_v1")]
        name = f"_handle_{name}_{event}"
        handle_func = getattr(self, name)
        proxy.dispatcher[event] = handle_func

    def run(self):
        """Run the main event loop until we get all workspace names."""
        print("Waiting for workspace names...")
        while not self.finished:
            # block=True waits for an event to arrive
            self.display.dispatch(block=False)
            time.sleep(1)

        print("\n--- Finished ---")
        print("Found workspaces:", self.workspace_names)

    def _handle_wl_registry_global(self, registry: WlRegistry, name: int, interface: str, version: int):
        print(f"Global: name: {name}, interface: {interface}, version: {version}")
        if interface == ExtWorkspaceManagerV1.name:
            self.workspace_manager = registry.bind(name, ExtWorkspaceManagerV1, version)
            self._reg_dispatcher(self.workspace_manager, "workspace_group")
            self._reg_dispatcher(self.workspace_manager, "workspace")
            self._reg_dispatcher(self.workspace_manager, "done")
            self._reg_dispatcher(self.workspace_manager, "finished")
        elif interface == ExtForeignToplevelListV1.name:
            self.toplevel_list = registry.bind(name, ExtForeignToplevelListV1, version)
            self._reg_dispatcher(self.toplevel_list, "toplevel")
            self._reg_dispatcher(self.toplevel_list, "finished")
            self.finished = True


    def _handle_wl_registry_global_remove(self, registry: WlRegistry, name: int):
        printf(f"_handle_wl_registry_global_remove: {registry}, {name}")

    def _handle_workspace_manager_workspace_group(self, workspace_manager, workspace_group):
        print(f"\nHandling workspace_manager workspace_group: {workspace_group}")
        self._reg_dispatcher(workspace_group, "capabilities")
        self._reg_dispatcher(workspace_group, "workspace_enter")
        self._reg_dispatcher(workspace_group, "workspace_leave")
        self._reg_dispatcher(workspace_group, "removed")

    def _handle_workspace_manager_workspace(self, workspace_manager, workspace):
        print(f"\nHandling workspace_manager workspace: {workspace}")
        self._reg_dispatcher(workspace, "id")
        self._reg_dispatcher(workspace, "name")
        self._reg_dispatcher(workspace, "coordinates")
        self._reg_dispatcher(workspace, "state")
        self._reg_dispatcher(workspace, "capabilities")
        self._reg_dispatcher(workspace, "removed")
        workspace.user_data = self.workspace_counter
        self.workspace_counter += 1

    def _handle_workspace_manager_done(self, workspace_manager):
        # print(f"\nHandling {workspace_manager} done")
        print(f"\nWorkspace Manager Done")

    def _handle_workspace_manager_finished(self, workspace_manager):
        print(f"\nHandling {workspace_manager} finished")

    def _handle_workspace_group_handle_capabilities(self, workspace_group, capabilities):
        print(f"\nHandling {workspace_group} capabilities {capabilities}")

    def _handle_workspace_group_handle_workspace_enter(self, workspace_group: ExtWorkspaceGroupHandleV1, workspace_handle: ExtWorkspaceHandleV1):
        print(f"\nHandling {workspace_group} workspace_enter {workspace_handle}")

    def _handle_workspace_group_handle_workspace_leave(self, workspace_group: ExtWorkspaceGroupHandleV1, workspace_handle: ExtWorkspaceHandleV1):
        print(f"\nHandling {workspace_group} workspace_leave {workspace_handle}")

    def _handle_workspace_group_handle_removed(self, group_handle: ExtWorkspaceGroupHandleV1):
        """All workspaces have been sent. We are finished."""
        print("Received 'removed' event for workspace group.")
        group_handle.destroy()

    def _handle_workspace_handle_id(self, workspace_handle: ExtWorkspaceHandleV1, id: str):
        print(f"  -> Got id: '{id}'")

    def _handle_workspace_handle_name(self, workspace_handle: ExtWorkspaceHandleV1, name: str):
        print(f"  -> Got name: '{name}'")
        self.workspace_names.append(name)

    def _handle_workspace_handle_coordinates(self, workspace_handle: ExtWorkspaceHandleV1, coordinates: list):
        print(f"  -> Got coordinates: '{coordinates}'")

    def _handle_workspace_handle_state(self, workspace_handle: ExtWorkspaceHandleV1, state: int):
        e = ExtWorkspaceHandleV1.state(state)
        print(f"  -> Got state: '{state}' <{e}>")

    def _handle_workspace_handle_capabilities(self, workspace_handle: ExtWorkspaceHandleV1, capabilities: int):
        e = ExtWorkspaceHandleV1.workspace_capabilities(capabilities)
        print(f"  -> Got capabilities: '{capabilities}' <{e}>")

    def _handle_workspace_handle_removed(self, workspace_handle: ExtWorkspaceHandleV1):
        print("Received 'removed' event for workspace handle.")
        workspace_handle.destroy()

    def _handle_foreign_toplevel_list_toplevel(self, toplevel_list, toplevel_handle):
        # print(f"\nNew Toplevel counter={self.toplevel_counter}")
        self._reg_dispatcher(toplevel_handle, "closed")
        self._reg_dispatcher(toplevel_handle, "title")
        self._reg_dispatcher(toplevel_handle, "app_id")
        self._reg_dispatcher(toplevel_handle, "identifier")
        self._reg_dispatcher(toplevel_handle, "done")
        toplevel_handle.user_data = {"counter": self.toplevel_counter}
        self.toplevel_counter += 1

    def _handle_foreign_toplevel_list_finished(self, toplevel_list):
        print(f"\nHandling {toplevel_list} finished")

    def _handle_foreign_toplevel_handle_closed(self, toplevel_handle):
        toplevel_handle.user_data["closed"] = true
        print(f"\nToplevel {toplevel_handle.user_data} closed")

    def _handle_foreign_toplevel_handle_title(self, toplevel_handle, title: str):
        toplevel_handle.user_data["title"] = title
        #print(f"\nToplevel {toplevel_handle.user_data} title [{title}]")

    def _handle_foreign_toplevel_handle_app_id(self, toplevel_handle, app_id: str):
        toplevel_handle.user_data["app_id"] = app_id
        #print(f"\nToplevel {toplevel_handle.user_data} app_id [{app_id}]")

    def _handle_foreign_toplevel_handle_identifier(self, toplevel_handle, identifier: str):
        toplevel_handle.user_data["identifier"] = identifier
        #print(f"\nToplevel {toplevel_handle.user_data} identifier [{identifier}]")

    def _handle_foreign_toplevel_handle_done(self, toplevel_handle):
        print(f"Toplevel {toplevel_handle.user_data} done")


def main():
    client = WorkspaceLister()
    client.run()
    client.display.disconnect()


if __name__ == '__main__':
    sys.exit(main())
