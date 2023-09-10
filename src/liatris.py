# SPDX-FileCopyrightText: Copyright © 2023 nixcapra
# SPDX-License-Identifier: MIT

import os

DB_ERROR = False
try:
    import liatris_db
except:
    DB_ERROR = True

import liatris_version
from models.liatris_model_settings import LiatrisSetting
from models.liatris_model_tasks import LiatrisTask
from models.liatris_model_items import LiatrisItem
from models.liatris_model_itemnotes import LiatrisItemNote

from datetime import timedelta
from datetime import date
from copy import copy as copy

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import Gdk

import warnings

warnings.filterwarnings("ignore")

nums = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]


class DbSettingsDefaults:
    DEFAULTSETTINGS = []

    def __init__(self):
        upcoming_th = LiatrisSetting()
        upcoming_th.Key = "UPCOMINGTHRESHOLD"
        upcoming_th.Value = "7"

        enable_nums = LiatrisSetting()
        enable_nums.Key = "ENABLENUMS"
        enable_nums.Value = "1"

        enable_monospace = LiatrisSetting()
        enable_monospace.Key = "ENABLEMONOSPACE"
        enable_monospace.Value = "0"

        self.DEFAULTSETTINGS.append(upcoming_th)
        self.DEFAULTSETTINGS.append(enable_nums)
        self.DEFAULTSETTINGS.append(enable_monospace)
        self.check_presence(self.DEFAULTSETTINGS)

    def check_presence(self, default_settings):
        settings_to_add = []
        for setting in default_settings:
            if not liatris_db.LiatrisSQLCore.Settings.get_setting_by_key(setting.Key):
                settings_to_add.append(setting)
        if len(settings_to_add) != 0:
            liatris_db.LiatrisSQLCore.insert_many(settings_to_add)


class Application(Gtk.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(
            application_id="org.nixcapra.liatris"
        )


class Main:
    def __init__(self):
        if DB_ERROR:
            e_diag = Gtk.MessageDialog(message_type=Gtk.MessageType.INFO, buttons=Gtk.ButtonsType.OK,
                                       text="Error accessing database.")
            e_diag.set_title("Error")
            e_diag.format_secondary_text(
                "Please make sure that the database at '/home/" + os.getlogin() + "/.liatris/liatrisdb' is accessible.")
            e_diag.run()
            e_diag.destroy()

            exit(1)

        DbSettingsDefaults()

        self.builder = Gtk.Builder()

        self.builder.add_from_file("liatris.glade")

        main_window = self.builder.get_object("MainWindow")
        main_window.connect("delete-event", Gtk.main_quit)
        main_window.set_title("Liatris")
        main_window.show_all()

        main_notebook = self.builder.get_object("MainNotebook")
        main_header_bar_label = self.builder.get_object("MainHeaderBarWindowTitleLabel")

        # Projects

        task_view_header_bar = self.builder.get_object("OnlyTaskHeaderBar")

        # What Task is currently clicked, this will tell us.

        task_view_header_bar.current_task = None

        task_name_label = self.builder.get_object("OnlyTaskNameLabel")
        task_main_list_box = self.builder.get_object("OnlyTaskMainListBox")
        task_main_list_box.set_activate_on_single_click(True)

        task_rename_entry = self.builder.get_object("OnlyTaskRenameEntry")
        task_rename_ok_button = self.builder.get_object("OnlyTaskHeaderRenameOkButton")
        task_rename_cancel_button = self.builder.get_object("OnlyTaskHeaderRenameCancelButton")
        task_rename_button = self.builder.get_object("OnlyTaskHeaderRenameButton")

        task_close_button = self.builder.get_object("OnlyTaskCloseButton")

        def task_rename_ok_button_trigger(self):
            task = copy(task_view_header_bar.current_task)
            if task is not None:
                task.TaskName = task_rename_entry.get_text().strip()

                if task_rename_ok_button.get_sensitive():
                    liatris_db.LiatrisSQLCore.Tasks.update_task(task)
                else:
                    call_ok_e_diag("Could not rename project.", "Error", "The provided project name was not valid.")

                rename_project_cancel_trigger(self)
                populate_project(task.TaskId)
                projects_search_bar.set_text("")
                load_tasks()

        def task_rename_entry_trigger(self):
            text = task_rename_entry.get_text()
            if text is not None:
                if text.strip() == "":
                    task_rename_ok_button.set_sensitive(False)
                else:
                    task_rename_ok_button.set_sensitive(True)

        task_rename_entry.connect("changed", task_rename_entry_trigger)

        def rename_project_cancel_trigger(self):
            task_name_label.show()
            task_rename_button.show()
            task_rename_entry.hide()
            task_rename_ok_button.hide()
            task_rename_cancel_button.hide()

        task_rename_cancel_button.connect("clicked", rename_project_cancel_trigger)
        task_rename_ok_button.connect("clicked", task_rename_ok_button_trigger)
        task_rename_entry.connect("activate", task_rename_ok_button_trigger)

        def rename_project_trigger(self):
            task_name_label.hide()
            task_rename_button.hide()
            task_rename_entry.show()
            task_rename_ok_button.show()
            task_rename_cancel_button.show()

            task_rename_entry.set_text(task_view_header_bar.current_task.TaskName)
            task_rename_entry.grab_focus()

        task_rename_button.connect("clicked", rename_project_trigger)

        def mark_item_trigger(self):
            item = copy(self.item)
            if self.get_active():
                item.ItemIsDone = True
            else:
                item.ItemIsDone = False

            if hasattr(self, 'TaskItem'):
                relevant_item = list(filter(lambda x: (x.ItemId == item.ItemId), self.TaskItem.Items))
                if len(relevant_item) != 0:
                    relevant_item = relevant_item[0]
                    relevant_item.ItemIsDone = item.ItemIsDone

                load_project_status_label(self.TaskItem)

            liatris_db.LiatrisSQLCore.Items.update_item(item)
            projects_search_bar.set_text("")
            load_tasks()

        def load_blank_page():
            main_notebook.hide()

        def task_close_trigger(self):
            load_blank_page()

        task_close_button.connect("clicked", task_close_trigger)

        def unload_blank_page():
            main_notebook.show()

        def populate_project_trigger(self, row):
            unload_blank_page()
            rename_project_cancel_trigger(self)
            main_notebook.set_current_page(0)
            populate_project(row.Id)

        def delete_project_trigger(self):
            e_diag = Gtk.MessageDialog(message_type=Gtk.MessageType.INFO, buttons=Gtk.ButtonsType.YES_NO,
                                       text="Do you wish to delete this project?")
            e_diag.set_title("Really delete?")
            e_diag.format_secondary_text("Once deleted, the project and all tasks within cannot be recovered.")
            if e_diag.run() == Gtk.ResponseType.YES:
                e_diag.destroy()
                liatris_db.LiatrisSQLCore.Tasks.delete_task(self.Id)
                load_blank_page()
                projects_search_bar.set_text("")
                load_tasks()
            else:
                e_diag.destroy()

        only_task_header_delete_button = self.builder.get_object("OnlyTaskHeaderDeleteButton")
        only_task_header_delete_button.connect("clicked", delete_project_trigger)

        def delete_item_trigger(self):
            e_diag = Gtk.MessageDialog(message_type=Gtk.MessageType.INFO, buttons=Gtk.ButtonsType.YES_NO,
                                       text="Do you wish to delete this task?")
            e_diag.set_title("Really delete?")
            e_diag.format_secondary_text("Once deleted, the task cannot be recovered.")
            if e_diag.run() == Gtk.ResponseType.YES:
                e_diag.destroy()
                liatris_db.LiatrisSQLCore.Items.delete_item(self.Id)
                unload_blank_page()
                rename_project_cancel_trigger(self)
                main_notebook.set_current_page(0)
                populate_project(self.PrjId)

                # Remember to reload
                projects_search_bar.set_text("")
                load_tasks()
            else:
                e_diag.destroy()

        project_status_label = self.builder.get_object("OnlyTaskHeaderStatusLabel")

        def load_project_status_label(task_item):
            total_items = len(task_item.ITEMS)
            total_finished_items = len(list(filter(lambda x: x.ItemIsDone is True, task_item.ITEMS)))

            if total_finished_items == total_items and total_finished_items != 0 and total_items != 0:
                project_status_label.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.20, 0.90, 0.20, 1.0))
            else:
                project_status_label.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.85, 0.08, 0.25, 1.0))
                project_status_label.set_text(str(total_finished_items) + "/" + str(total_items))

            project_status_label.set_text(str(total_finished_items) + "/" + str(total_items))

        def populate_project(TaskId):
            task_item = liatris_db.LiatrisSQLCore.Tasks.produce_task_item_by_task_id(TaskId)
            task_view_header_bar.TaskItem = task_item
            task_view_header_bar.current_task = task_item.TASK
            only_task_header_delete_button.Id = task_item.TASK.TaskId
            task_name_label.set_text(task_view_header_bar.current_task.TaskName)
            load_project_status_label(task_item)

            for child in task_main_list_box.get_children():
                child.destroy()

            task_item.ITEMS = sorted(task_item.ITEMS, key=lambda x: (x.ItemDate is None, x.ItemDate))
            task_item.ITEMS.reverse()

            for item in task_item.ITEMS:
                if item.ItemIsDone:
                    continue

                row = Gtk.ListBoxRow()
                hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=100)
                hbox.set_margin_top(10)
                hbox.set_margin_bottom(10)
                row.add(hbox)
                row.Id = item.ItemId
                label = Gtk.Label()
                label.set_text(str(item.ItemTitle))

                check_button = Gtk.CheckButton()
                check_button.item = item
                check_button.task_item = task_item

                check_button.connect("toggled", mark_item_trigger)

                delete_button = Gtk.Button()
                delete_button.Id = item.ItemId
                delete_button.PrjId = TaskId
                trash_icon = Gtk.Image()
                trash_icon = trash_icon.new_from_icon_name("user-trash-symbolic", Gtk.IconSize.MENU)
                delete_button.set_image(trash_icon)
                delete_button.set_tooltip_text("Delete Task")
                delete_button.set_always_show_image(True)
                delete_button.set_relief(Gtk.ReliefStyle.NONE)
                delete_button.connect("clicked", delete_item_trigger)
                hbox.pack_start(check_button, False, False, 10)
                hbox.pack_start(label, False, False, 10)
                hbox.pack_end(delete_button, False, False, 10)

                if item.ItemDate is not None:
                    deadline_label = Gtk.Label()
                    if item.ItemDate.date() < date.today():
                        deadline_label.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.85, 0.08, 0.25, 1.0))
                        deadline_label.set_text(str(item.ItemDate.date()))
                    else:
                        deadline_label.set_text(str(item.ItemDate.date()))
                    hbox.pack_end(deadline_label, False, False, 10)

                task_main_list_box.insert(row, 0)
                task_main_list_box.show_all()

            task_main_list_box.connect("row-activated", load_item_view)

        # View in Logbook

        def only_task_logbook_button_trigger(self):
            populate_task_items([task_view_header_bar.TaskItem],
                                'Logbook for Project "' + str(task_view_header_bar.TaskItem.TASK.TaskName) + '"')

        only_task_logbook_button = self.builder.get_object("OnlyTaskLogbookButton")
        only_task_logbook_button.connect("clicked", only_task_logbook_button_trigger)

        # Projects Sidebar

        projects_list_box = self.builder.get_object("ProjectsSidebarListBox")

        def filter_tasks(tasks):
            real_tasks = []
            for task in tasks:
                if task.TaskName is not None and task.TaskId is not None:
                    real_tasks.append(task)
            return real_tasks

        def task_search_trigger(self):
            load_tasks(str(self.get_text()))

        def load_tasks(search=None):
            tasks = None
            if search is None or search.strip() == "":

                tasks = liatris_db.LiatrisSQLCore.Tasks.get_all_tasks()
            else:
                tasks = liatris_db.LiatrisSQLCore.Tasks.search_tasks(search)
            tasks = filter_tasks(tasks)

            for child in projects_list_box.get_children():
                child.destroy()

            for task in tasks:
                items = liatris_db.LiatrisSQLCore.Tasks.produce_task_item_by_task_id(task.TaskId).ITEMS

                total_items = len(items)
                total_finished_items = len(list(filter(lambda x: x.ItemIsDone is True, items)))

                row = Gtk.ListBoxRow()
                hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
                hbox.set_margin_top(5)
                hbox.set_margin_bottom(5)
                row.add(hbox)
                row.Id = task.TaskId
                row.set_tooltip_text(str(task.TaskName))
                label = Gtk.Label()
                label.set_text(str(task.TaskName))

                stats_label = Gtk.Label()
                if total_finished_items == total_items and total_finished_items != 0 and total_items != 0:
                    stats_label.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.20, 0.90, 0.20, 1.0))
                else:
                    stats_label.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.85, 0.08, 0.25, 1.0))

                stats_label.set_text(str(total_finished_items) + "/" + str(total_items))
                hbox.pack_start(label, False, False, 5)
                hbox.pack_end(stats_label, False, False, 5)
                projects_list_box.insert(row, 0)
                projects_list_box.show_all()

            if len(tasks) == 1 and search != None:
                row = projects_list_box.get_row_at_index(0)
                projects_list_box.select_row(row)
                populate_project_trigger(self, row)

            load_upcoming_nums()
            load_today_nums()

        projects_list_box.connect("row-activated", populate_project_trigger)

        projects_search_bar = self.builder.get_object("ProjectsSearchEntry")
        projects_search_bar.connect("changed", task_search_trigger)

        def clear_search_trigger(self):
            projects_search_bar.set_text("")
            projects_search_bar.grab_focus()

        project_search_clear_button = self.builder.get_object("ProjectsSidebarClearSearchTextButton")
        project_search_clear_button.connect("clicked", clear_search_trigger)

        def call_ok_e_diag(text, title, sec_text):
            e_diag = Gtk.MessageDialog(message_type=Gtk.MessageType.INFO, buttons=Gtk.ButtonsType.OK, text=text)
            e_diag.set_title(title)
            e_diag.format_secondary_text(sec_text)
            e_diag.run()
            e_diag.destroy()

        # Add Project Popover

        add_project_popover = self.builder.get_object("AddProjectPopover")
        add_project_popover_cancel_button = self.builder.get_object("AddProjectCancelButton")
        add_project_popover_add_button = self.builder.get_object("AddProjectAddButton")
        add_project_popover_add_text_entry = self.builder.get_object("AddProjectPopoverProjectNameTextEntry")

        add_project_popover_add_button.set_sensitive(False)

        def add_project_name_entry_trigger(self):
            text = add_project_popover_add_text_entry.get_text()
            if text != None:
                if text.strip() == "":
                    add_project_popover_add_button.set_sensitive(False)
                else:
                    add_project_popover_add_button.set_sensitive(True)

        add_project_popover_add_text_entry.connect("changed", add_project_name_entry_trigger)

        def popover_cancel_trigger(self):
            add_project_popover_add_text_entry.set_text("")
            add_project_popover.popdown()

        def add_project_trigger(self):
            project_name = add_project_popover_add_text_entry.get_text()
            if project_name is not None:
                if project_name.strip() == "":
                    call_ok_e_diag("Could not add project.", "Error", "The provided project name was not valid.")
                    popover_cancel_trigger(self)
                    return

            new_task = LiatrisTask()
            new_task.TaskName = project_name.strip()
            liatris_db.LiatrisSQLCore.insert(new_task)

            # Reset Search Field and Load Tasks anew.
            projects_search_bar.set_text("")
            load_tasks()
            popover_cancel_trigger(self)

        add_project_popover_cancel_button.connect("clicked", popover_cancel_trigger)
        add_project_popover_add_button.connect("clicked", add_project_trigger)
        add_project_popover_add_text_entry.connect("activate", add_project_trigger)

        # Add Task Popover

        add_task_popover = self.builder.get_object("AddTaskPopover")
        add_task_popover_cancel_button = self.builder.get_object("AddTaskCancelButton")
        add_task_popover_add_button = self.builder.get_object("AddTaskAddButton")
        add_task_popover_add_text_entry = self.builder.get_object("AddTaskPopoverTaskNameTextEntry")

        add_task_popover_add_button.set_sensitive(False)

        def add_task_name_entry_trigger(self):
            text = add_task_popover_add_text_entry.get_text()
            if text is not None:
                if text.strip() == "":
                    add_task_popover_add_button.set_sensitive(False)
                else:
                    add_task_popover_add_button.set_sensitive(True)

        add_task_popover_add_text_entry.connect("changed", add_task_name_entry_trigger)

        def add_task_popover_cancel_trigger(self):
            add_task_popover_add_text_entry.set_text("")
            add_task_popover.popdown()

        def reload_current_project():
            populate_project(task_view_header_bar.current_task.TaskId)

        def add_task_trigger(self):
            task_name = add_task_popover_add_text_entry.get_text()
            if task_name is not None:
                if task_name.strip() == "":
                    call_ok_e_diag("Could not add task.", "Error", "The provided task name was not valid.")
                    popover_cancel_trigger(self)
                    return

            new_task = LiatrisItem()
            new_task.ItemIsDone = False
            new_task.ItemDate = None
            new_task.ItemTitle = task_name
            new_task.TaskId = task_view_header_bar.current_task.TaskId
            liatris_db.LiatrisSQLCore.insert(new_task)

            # Reset Search Field and Load Items anew.
            projects_search_bar.set_text("")
            load_tasks()
            reload_current_project()
            add_task_popover_cancel_trigger(self)

        add_task_popover_cancel_button.connect("clicked", add_task_popover_cancel_trigger)
        add_task_popover_add_button.connect("clicked", add_task_trigger)
        add_task_popover_add_text_entry.connect("activate", add_task_trigger)

        # Item Task View

        task_item_tree_label = self.builder.get_object("ProjectTaskTreeNameLabel")
        task_item_list_view = self.builder.get_object("ProjectTaskTreeListBox")

        task_item_list_close_button = self.builder.get_object("ProjectTaskTreeCloseButton")

        def display_children_list_box_trigger(self):
            if self.LISTBOX.props.visible:
                image = Gtk.Image()
                image = image.new_from_icon_name("go-up-symbolic", Gtk.IconSize.MENU)
                self.set_image(image)

                self.LISTBOX.hide()
            else:
                image = Gtk.Image()
                image = image.new_from_icon_name("go-down-symbolic", Gtk.IconSize.MENU)
                self.set_image(image)
                self.LISTBOX.show()

        def load_item_view(self, row):
            populate_item_detail_view(row.Id)

        def populate_task_items(task_items, title):
            unload_blank_page()
            main_notebook.set_current_page(1)
            # Set title
            task_item_tree_label.set_text(str(title))

            for child in task_item_list_view.get_children():
                child.destroy()

            for task_item in task_items:
                if task_item.TASK.TaskName is None:
                    continue
                # Add Task Parent
                row = Gtk.ListBoxRow()
                hbox = Gtk.Grid()
                hbox.set_margin_top(10)
                hbox.set_margin_bottom(10)
                row.add(hbox)
                row.Id = task_item.TASK.TaskId
                label = Gtk.Label()
                label.set_text(str(task_item.TASK.TaskName))
                label.set_margin_start(5)

                children_list_box = Gtk.ListBox()
                children_list_box.set_margin_start(90)
                children_list_box.set_margin_top(10)
                children_list_box.set_margin_end(10)
                children_list_box.set_hexpand(True)
                children_list_box.connect("row-activated", load_item_view)

                expand_button = Gtk.Button()
                expand_image = Gtk.Image()
                expand_image = expand_image.new_from_icon_name("go-down-symbolic", Gtk.IconSize.MENU)
                expand_button.set_image(expand_image)
                expand_button.set_tooltip_text("Expand Project")
                expand_button.set_always_show_image(True)
                expand_button.set_relief(Gtk.ReliefStyle.NONE)
                expand_button.LISTBOX = children_list_box
                expand_button.connect("clicked", display_children_list_box_trigger)

                # Add Children
                if len(task_item.ITEMS) != 0:

                    task_item.ITEMS = sorted(task_item.ITEMS, key=lambda x: (x.ItemDate is None, x.ItemDate))
                    task_item.ITEMS.reverse()

                    for item in task_item.ITEMS:
                        trow = Gtk.ListBoxRow()
                        th_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
                        th_box.set_margin_top(10)
                        th_box.set_margin_bottom(10)
                        trow.add(th_box)
                        trow.Id = item.ItemId
                        t_label = Gtk.Label()
                        t_label.set_text(str(item.ItemTitle))

                        t_check_button = Gtk.CheckButton()
                        t_check_button.item = item

                        if item.ItemIsDone:
                            t_check_button.set_active(True)

                        t_check_button.connect("toggled", mark_item_trigger)

                        th_box.pack_start(t_check_button, False, False, 10)
                        th_box.pack_start(t_label, False, False, 10)

                        if item.ItemDate is not None:
                            t_deadline_label = Gtk.Label()
                            if item.ItemDate.date() < date.today():
                                t_deadline_label.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.85, 0.08, 0.25, 1.0))
                                t_deadline_label.set_text(str(item.ItemDate.date()))
                            else:
                                t_deadline_label.set_text(str(item.ItemDate.date()))

                            th_box.pack_end(t_deadline_label, False, False, 10)

                        children_list_box.insert(trow, 0)
                        children_list_box.show_all()

                box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
                if len(task_item.ITEMS) != 0:
                    box.pack_start(expand_button, False, False, 5)

                box.pack_start(label, False, False, 5)
                hbox.attach(box, 0, 0, 1, 1)

                # Attach ListBox only if it is populated
                if len(task_item.ITEMS) != 0:
                    hbox.attach(children_list_box, 0, 1, 1, 1)

                task_item_list_view.insert(row, 0)
                task_item_list_view.show_all()

        # Search

        def search_entry_trigger(self):
            search_text = search_entry.get_text().strip()
            if search_text != "":
                result_task_items = liatris_db.LiatrisSQLCore.Tasks.search_task_items(search_text)
                populate_task_items(result_task_items, 'Search "' + search_text + '"')
            else:
                load_blank_page()

        search_entry = self.builder.get_object("HeaderSearchBar")
        search_entry.connect("changed", search_entry_trigger)
        search_entry.connect("activate", search_entry_trigger)

        def item_task_close_trigger(self):
            search_entry.set_text("")
            load_blank_page()

        task_item_list_close_button.connect("clicked", item_task_close_trigger)

        # Logbook

        logbook_button = self.builder.get_object("LogbookButton")

        def populate_logbook_trigger(self):
            all_task_items = liatris_db.LiatrisSQLCore.Tasks.produce_all_task_items()

            new_task_items = []

            for task_item in all_task_items:
                if task_item.TASK.TaskName is None:
                    continue

                new_items = []
                for item in task_item.ITEMS:
                    if item.ItemIsDone:
                        new_items.append(item)

                task_item.ITEMS = new_items

                if len(new_items) != 0:
                    new_task_items.append(task_item)

            populate_task_items(new_task_items, "Logbook")

        logbook_button.connect("clicked", populate_logbook_trigger)

        # Upcoming

        upcoming_button = self.builder.get_object("UpcomingButton")

        def load_upcoming_nums():
            is_enabled = liatris_db.LiatrisSQLCore.Settings.get_setting_by_key("ENABLENUMS")
            if is_enabled:
                if is_enabled.Value == "1":
                    all_task_items = liatris_db.LiatrisSQLCore.Tasks.produce_all_task_items()

                    counter = 0

                    for task_item in all_task_items:
                        if task_item.TASK.TaskName is None:
                            continue

                        for item in task_item.ITEMS:
                            if item.ItemDate is None or item.ItemIsDone is True:
                                continue
                            if date.today() < item.ItemDate.date() < date.today() + timedelta(
                                    days=int(liatris_db.LiatrisSQLCore.Settings.get_setting_by_key(
                                        "UPCOMINGTHRESHOLD").Value)):
                                counter += 1

                    if counter != 0:
                        upcoming_button.set_label("Upcoming • (" + str(counter) + ")")
                    else:
                        upcoming_button.set_label("Upcoming")
                else:
                    upcoming_button.set_label("Upcoming")

        def populate_upcoming_trigger(self):
            all_task_items = liatris_db.LiatrisSQLCore.Tasks.produce_all_task_items()

            new_task_items = []

            for task_item in all_task_items:
                if task_item.TASK.TaskName is None:
                    continue

                new_items = []
                for item in task_item.ITEMS:
                    if item.ItemDate is None or item.ItemIsDone is True:
                        continue
                    if date.today() < item.ItemDate.date() < date.today() + timedelta(
                            days=int(liatris_db.LiatrisSQLCore.Settings.get_setting_by_key("UPCOMINGTHRESHOLD").Value)):
                        new_items.append(item)

                task_item.ITEMS = new_items

                if len(new_items) != 0:
                    new_task_items.append(task_item)

            populate_task_items(new_task_items, "Upcoming")

        upcoming_button.connect("clicked", populate_upcoming_trigger)

        # Today

        today_button = self.builder.get_object("TodayButton")

        def load_today_nums():
            is_enabled = liatris_db.LiatrisSQLCore.Settings.get_setting_by_key("ENABLENUMS")
            if is_enabled:
                if is_enabled.Value == "1":
                    all_task_items = liatris_db.LiatrisSQLCore.Tasks.produce_all_task_items()

                    counter = 0

                    for task_item in all_task_items:
                        if task_item.TASK.TaskName is None:
                            continue

                        for item in task_item.ITEMS:
                            if item.ItemDate is None or item.ItemIsDone is True:
                                continue
                            if item.ItemDate.date() == date.today() or item.ItemDate.date() < date.today():
                                counter += 1

                    if counter != 0:
                        today_button.set_label("Today • (" + str(counter) + ")")
                        main_header_bar_label.set_text("Liatris (" + str(counter) + ")")
                        main_window.set_title("Liatris (" + str(counter) + ")")
                    else:
                        today_button.set_label("Today")
                        main_header_bar_label.set_text("Liatris")
                        main_window.set_title("Liatris")
                else:
                    today_button.set_label("Today")
                    main_header_bar_label.set_text("Liatris")
                    main_window.set_title("Liatris")

        def populate_today_trigger(self):
            all_task_items = liatris_db.LiatrisSQLCore.Tasks.produce_all_task_items()

            new_task_items = []

            for task_item in all_task_items:
                if task_item.TASK.TaskName is None:
                    continue

                new_items = []
                for item in task_item.ITEMS:
                    if item.ItemDate is None or item.ItemIsDone is True:
                        continue
                    if item.ItemDate.date() == date.today() or item.ItemDate.date() < date.today():
                        new_items.append(item)

                task_item.ITEMS = new_items

                if len(new_items) != 0:
                    new_task_items.append(task_item)

            populate_task_items(new_task_items, "Today")

        today_button.connect("clicked", populate_today_trigger)

        # Someday

        someday_button = self.builder.get_object("SomedayButton")

        def populate_someday_trigger(self):
            all_task_items = liatris_db.LiatrisSQLCore.Tasks.produce_all_task_items()

            new_task_items = []

            for task_item in all_task_items:
                if task_item.TASK.TaskName is None:
                    continue

                new_items = []
                for item in task_item.ITEMS:
                    if item.ItemIsDone:
                        continue
                    if item.ItemDate is None:
                        new_items.append(item)

                task_item.ITEMS = new_items

                if len(new_items) != 0:
                    new_task_items.append(task_item)

            populate_task_items(new_task_items, "Someday")

        someday_button.connect("clicked", populate_someday_trigger)

        # Item Detail View

        item_detail_header_bar = self.builder.get_object("TaskDetailEditHeaderBar")
        item_name_label = self.builder.get_object("TaskDetailEditTaskNameLabel")

        item_rename_entry = self.builder.get_object("TaskDetailEditRenameEntry")
        item_rename_ok_button = self.builder.get_object("TaskDetailEditRenameOkButton")
        item_rename_cancel_button = self.builder.get_object("TaskDetailEditRenameCancelButton")
        item_rename_button = self.builder.get_object("TaskDetailEditRenameButton")

        task_detail_item_is_done_toggle = self.builder.get_object("TaskDetailEditDoneCheckButton")
        task_detail_item_is_done_toggle.connect("toggled", mark_item_trigger)

        task_detail_deadline_menu_button = self.builder.get_object("DatePickerMenuButton")
        task_detail_deadline_menu_button_label = self.builder.get_object("DatePickerMenuButtonDateLabel")

        task_detail_deadline_date_picker_popover = self.builder.get_object("DatePickerPopover")
        task_detail_deadline_date_picker_calendar = self.builder.get_object("DatePickerCalendar")
        task_detail_deadline_date_picker_ok_button = self.builder.get_object("DatePickerCalendarOkButton")
        task_detail_deadline_date_picker_cancel_button = self.builder.get_object("DatePickerCalendarCancelButton")
        task_detail_deadline_date_picker_deadline_button = self.builder.get_object("DatePickerRemoveDeadlineButton")

        task_detail_item_deadline_toggle = self.builder.get_object("TaskDetailEditDateCheckButton")

        task_detail_item_text_view = self.builder.get_object("TaskDetailEditTextView")

        task_detail_close_button = self.builder.get_object("TaskDetailEditCloseButton")
        task_detail_edit_delete_button = self.builder.get_object("TaskDetailEditDeleteButton")

        def task_detail_close_trigger(self):
            unload_blank_page()
            rename_project_cancel_trigger(self)
            main_notebook.set_current_page(0)
            populate_project(item_detail_header_bar.ItemToEdit.TaskId)

        task_detail_close_button.connect("clicked", task_detail_close_trigger)

        def set_calendar_date(date):
            task_detail_deadline_date_picker_calendar.select_month(date.month - 1, date.year)
            task_detail_deadline_date_picker_calendar.select_day(date.day)

        def get_calendar_date():
            new_date = task_detail_deadline_date_picker_calendar.get_date()
            return date(new_date.year, new_date.month + 1, new_date.day)

        def calendar_ok_button_trigger(self):
            if not task_detail_item_deadline_toggle.get_active():
                return

            s_date = get_calendar_date()

            item_detail_header_bar.ItemToEdit.ItemDate = s_date
            liatris_db.LiatrisSQLCore.Items.update_item(item_detail_header_bar.ItemToEdit)
            item_detail_reload_item(item_detail_header_bar.ItemToEdit.ItemId)
            set_calendar_date(s_date)
            load_tasks()
            reload_calendar_button_label()
            task_detail_deadline_date_picker_popover.popdown()

        def calendar_cancel_button_trigger(self):
            if item_detail_header_bar.ItemToEdit.ItemDate is not None:
                set_calendar_date(item_detail_header_bar.ItemToEdit.ItemDate)
            else:
                set_calendar_date(date.today())

            task_detail_deadline_date_picker_popover.popdown()

        def reload_calendar_button_label():
            task_detail_deadline_menu_button_label.set_text(str(get_calendar_date()))

        def set_select_date_button_label():
            task_detail_deadline_menu_button_label.set_text("Select date...")

        def disable_deadline_toggle_trigger(self):
            item_detail_header_bar.ItemToEdit.ItemDate = None
            liatris_db.LiatrisSQLCore.Items.update_item(item_detail_header_bar.ItemToEdit)
            set_select_date_button_label()
            task_edit_toggle_deadline(False)
            set_calendar_date(date.today())
            task_detail_deadline_date_picker_popover.popdown()
            item_detail_reload_item(item_detail_header_bar.ItemToEdit.ItemId)
            load_tasks()

        task_detail_deadline_date_picker_deadline_button.connect("clicked", disable_deadline_toggle_trigger)

        task_detail_deadline_date_picker_cancel_button.connect("clicked", calendar_cancel_button_trigger)
        task_detail_deadline_date_picker_ok_button.connect("clicked", calendar_ok_button_trigger)

        def task_edit_toggle_deadline(flag):
            if flag:
                task_detail_item_deadline_toggle.set_active(True)
                task_detail_item_deadline_toggle.set_sensitive(False)
                task_detail_deadline_menu_button.show()
            else:
                task_detail_item_deadline_toggle.set_active(False)
                task_detail_item_deadline_toggle.set_sensitive(True)
                task_detail_deadline_menu_button.hide()

        def task_detail_item_deadline_toggle_trigger(self):
            if task_detail_item_deadline_toggle.get_active():
                task_edit_toggle_deadline(True)
            else:
                task_edit_toggle_deadline(False)

        def task_detail_item_delete_trigger(self):
            delete_item_trigger(self)

        task_detail_edit_delete_button.connect("clicked", task_detail_item_delete_trigger)

        def item_detail_reload_item(item_id):
            item = liatris_db.LiatrisSQLCore.Items.get_item_by_id(item_id)
            item_detail_header_bar.ItemToEdit = copy(item)
            item_detail_header_bar.CurrentItem = item
            return item

        def load_item_note():
            item_note = liatris_db.LiatrisSQLCore.ItemNotes.get_item_note_by_item_id(
                item_detail_header_bar.CurrentItem.ItemId)

            if not item_note:
                item_note = LiatrisItemNote()
                item_note.ItemId = item_detail_header_bar.CurrentItem.ItemId
                item_note.NoteContent = ""
                liatris_db.LiatrisSQLCore.insert(item_note)

            buffer = Gtk.TextBuffer()

            monospace_setting = liatris_db.LiatrisSQLCore.Settings.get_setting_by_key("ENABLEMONOSPACE")

            if monospace_setting is not None:
                if monospace_setting.Value == "1":
                    task_detail_item_text_view.set_monospace(True)
                else:
                    task_detail_item_text_view.set_monospace(False)

            buffer.set_text(item_note.NoteContent)
            task_detail_item_text_view.set_buffer(buffer)

            return item_note

        def item_note_text_trigger(self_a, self_b):
            buffer = task_detail_item_text_view.get_buffer()
            buffer_text = str(buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False))
            if item_detail_header_bar.CurrentItemNote.NoteContent == buffer_text:
                return

            item_detail_header_bar.CurrentItemNote.NoteContent = buffer_text

            liatris_db.LiatrisSQLCore.ItemNotes.update_item_note(item_detail_header_bar.CurrentItemNote)
            item_detail_reload_item(item_detail_header_bar.ItemToEdit.ItemId)

        task_detail_item_text_view.connect("key-release-event", item_note_text_trigger)

        def populate_item_detail_view(item_id):
            rename_item_cancel_trigger(self)
            item = item_detail_reload_item(item_id)
            if item is not None:

                unload_blank_page()
                main_notebook.set_current_page(2)

                item_name_label.set_text(item.ItemTitle)

                task_detail_item_is_done_toggle.item = item

                task_detail_edit_delete_button.Id = item.ItemId
                task_detail_edit_delete_button.PrjId = item.TaskId
                task_detail_item_is_done_toggle.grab_focus()

                if item.ItemIsDone:
                    task_detail_item_is_done_toggle.set_active(True)
                else:
                    task_detail_item_is_done_toggle.set_active(False)

                if item.ItemDate is None:
                    task_edit_toggle_deadline(False)
                else:
                    task_edit_toggle_deadline(True)

                # Calendar init
                if item.ItemDate is not None:
                    set_calendar_date(item.ItemDate.date())
                    reload_calendar_button_label()
                else:
                    set_calendar_date(date.today())
                    set_select_date_button_label()

                item_detail_header_bar.CurrentItemNote = load_item_note()

        task_detail_item_deadline_toggle.connect("toggled", task_detail_item_deadline_toggle_trigger)

        def item_rename_ok_button_trigger(self):
            item = copy(item_detail_header_bar.CurrentItem)
            if item is not None:
                item.ItemTitle = item_rename_entry.get_text().strip()

                if item_rename_ok_button.get_sensitive():
                    liatris_db.LiatrisSQLCore.Items.update_item(item)
                else:
                    call_ok_e_diag("Could not rename task.", "Error", "The provided task name was not valid.")

                rename_project_cancel_trigger(self)
                populate_item_detail_view(item.ItemId)
                projects_search_bar.set_text("")
                load_tasks()

        def item_rename_entry_trigger(self):
            text = item_rename_entry.get_text()
            if text is not None:
                if text.strip() == "":
                    item_rename_ok_button.set_sensitive(False)
                else:
                    item_rename_ok_button.set_sensitive(True)

        item_rename_entry.connect("changed", item_rename_entry_trigger)

        def rename_item_cancel_trigger(self):
            item_name_label.show()
            item_rename_button.show()
            item_rename_entry.hide()
            item_rename_ok_button.hide()
            item_rename_cancel_button.hide()

        item_rename_cancel_button.connect("clicked", rename_item_cancel_trigger)
        item_rename_ok_button.connect("clicked", item_rename_ok_button_trigger)
        item_rename_entry.connect("activate", item_rename_ok_button_trigger)

        def rename_item_trigger(self):
            item_name_label.hide()
            item_rename_button.hide()
            item_rename_entry.show()
            item_rename_ok_button.show()
            item_rename_cancel_button.show()

            item_rename_entry.set_text(item_detail_header_bar.CurrentItem.ItemTitle)
            item_rename_entry.grab_focus()

        item_rename_button.connect("clicked", rename_item_trigger)

        # Settings

        main_settings_window = self.builder.get_object("LiatrisSettingsWindow")
        main_settings_back_button = self.builder.get_object("LiatrisSettingsBackButton")
        main_settings_upcoming_entry = self.builder.get_object("LiatrisSettingsUpcomingDaysEntry")
        main_settings_warnings_toggle = self.builder.get_object("LiatrisSettingsEnableWarningCheckButton")
        main_settings_monospace_toggle = self.builder.get_object("LiatrisSettingsEnableMonospaceCheckButton")

        def upcoming_threshold_integrity(value):
            if int(value) > 70:
                return 70
            if int(value) < 1:
                return 1

            return value

        def main_settings_upcoming_entry_trigger_replace_nums(self):
            text = self.get_text()
            new_text = []
            text_chars = [char for char in text]
            for item in text_chars:
                if item in nums:
                    new_text.append(item)

            self.set_text(''.join(new_text))

        def main_settings_upcoming_entry_trigger(self):
            main_settings_upcoming_entry_trigger_replace_nums(self)
            if self.NoTrigger == True or self.get_text().strip() == "":
                return

            self.NoTrigger = True
            self.set_text(str(upcoming_threshold_integrity(self.get_text())))
            self.NoTrigger = False

            upcoming_setting = liatris_db.LiatrisSQLCore.Settings.get_setting_by_key("UPCOMINGTHRESHOLD")
            upcoming_setting.Value = str(upcoming_threshold_integrity(self.get_text()))

            liatris_db.LiatrisSQLCore.Settings.update_setting(upcoming_setting)
            load_tasks()
            return True

        main_settings_upcoming_entry.connect("changed", main_settings_upcoming_entry_trigger)

        def MAINSETTINGSWARNINGSTOGGLETRIGGER(self):
            if self.NoTrigger == True:
                return

            warnings_setting = liatris_db.LiatrisSQLCore.Settings.get_setting_by_key("ENABLENUMS")
            if self.get_active():
                warnings_setting.Value = "1"
            else:
                warnings_setting.Value = "0"

            liatris_db.LiatrisSQLCore.Settings.update_setting(warnings_setting)
            load_tasks()
            return True

        main_settings_warnings_toggle.connect("toggled", MAINSETTINGSWARNINGSTOGGLETRIGGER)

        def main_settings_monospace_toggle_trigger(self):
            monospace_setting = liatris_db.LiatrisSQLCore.Settings.get_setting_by_key("ENABLEMONOSPACE")

            if self.get_active() == True:
                monospace_setting.Value = "1"
            else:
                monospace_setting.Value = "0"

            liatris_db.LiatrisSQLCore.Settings.update_setting(monospace_setting)
            return True

        main_settings_monospace_toggle.connect("toggled", main_settings_monospace_toggle_trigger)

        def open_settings(self):
            upcoming_setting = liatris_db.LiatrisSQLCore.Settings.get_setting_by_key("UPCOMINGTHRESHOLD")
            warnings_setting = liatris_db.LiatrisSQLCore.Settings.get_setting_by_key("ENABLENUMS")
            monospace_setting = liatris_db.LiatrisSQLCore.Settings.get_setting_by_key("ENABLEMONOSPACE")

            if upcoming_setting is None or warnings_setting is None or monospace_setting is None:
                return

            main_settings_upcoming_entry.NoTrigger = True
            main_settings_upcoming_entry.set_text(upcoming_threshold_integrity(upcoming_setting.Value))
            main_settings_upcoming_entry.NoTrigger = False

            main_settings_warnings_toggle.NoTrigger = True
            try:
                if int(warnings_setting.Value) == 1:
                    main_settings_warnings_toggle.set_active(True)
                else:
                    main_settings_warnings_toggle.set_active(False)
            except:
                main_settings_warnings_toggle.set_active(True)

            main_settings_warnings_toggle.NoTrigger = False

            try:
                if int(monospace_setting.Value) == 1:
                    main_settings_monospace_toggle.set_active(True)
                else:
                    main_settings_monospace_toggle.set_active(False)
            except:
                main_settings_monospace_toggle.set_active(False)

            main_settings_upcoming_entry.grab_focus()
            main_settings_window.show()
            return True

        def close_settings(self):
            main_settings_window.hide()
            return True

        main_settings_back_button.connect("clicked", close_settings)

        # Keyboard Shortcuts

        def key_press_handler(window, event):
            keyname = Gdk.keyval_name(event.keyval)

            if Gdk.ModifierType.CONTROL_MASK == event.state:
                if keyname == "q":
                    Gtk.main_quit()
                if keyname == "w":
                    load_blank_page()
                if keyname == "p":
                    projects_search_bar.set_text("")
                    projects_search_bar.grab_focus()
                if keyname == "s":
                    search_entry.set_text("")
                    search_entry.grab_focus()
                if keyname == "t":
                    populate_today_trigger(self)
                if keyname == "f":
                    populate_upcoming_trigger(self)
                if keyname == "o":
                    populate_someday_trigger(self)
                if keyname == "l":
                    populate_logbook_trigger(self)

        main_window.connect("key-press-event", key_press_handler)

        # About

        about_diag = self.builder.get_object("AboutDialog")

        def show_about(self):
            about_diag.show()
            return True

        def hide_about(selfA, selfB):
            about_diag.hide()
            return True

        about_diag.connect("delete-event", hide_about)
        about_diag.hide()

        about_link = self.builder.get_object("AboutLink")
        about_diag.set_version(liatris_version.LIATRIS_VERSION)
        about_link.connect("clicked", show_about)

        settings_link = self.builder.get_object("SettingsLink")
        settings_link.connect("clicked", open_settings)

        def init_window():
            load_blank_page()
            load_tasks()
            load_upcoming_nums()
            load_today_nums()

        init_window()


if __name__ == "__main__":
    try:
        application = Application()
        main = Main()
        Gtk.init()
        Gtk.main()
    except KeyboardInterrupt:
        pass
