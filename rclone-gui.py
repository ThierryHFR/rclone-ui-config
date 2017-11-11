#!/usr/bin/env python3 
 
from __future__ import print_function
import subprocess
import json
import gi
import time
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

try:
    from types import SimpleNamespace as Namespace
except ImportError:
    # Python 2.x fallback
    from argparse import Namespace

class ComboBoxWindow(Gtk.Window):

    def frameBoxVertical(self, labeFrame):
        vboxFrame = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        frameNewRemote = Gtk.Frame()
        frameNewRemote.show()
        frameNewRemote.add(vboxFrame)
        frameNewRemote.set_label(labeFrame)
        self.vbox.pack_start(frameNewRemote, False, False, 0)
        return vboxFrame

    def on_delete_remote(self, button):
        exe = ''
        tree_iter = None
        selection = self.tree.get_selection()
        model, paths = selection.get_selected_rows()
        for path in paths:
            tree_iter = model.get_iter(path)
        exe = model.get_value(tree_iter,0) 
        print(exe)
        try:
            py2code = subprocess.check_call(['rclone', 'config', 'delete', exe])
            if py2code  == 0:
                model.remove(tree_iter)
                msg = 'Your remote has been successfully removed...'
            else:
                msg = 'Failed to remove your remote...'
        except subprocess.CalledProcessError as e:
            msg = 'Failed to remove your remote...'
        dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, msg)
        dialog.run()
        dialog.destroy()

    def on_new_remote(self, button):
        opts = []
        exe = ''
        msg = ''
        for obj in self.listOptionsObj:
            if obj.get_text_length():
                opts.append(obj.get_name())
                opts.append(obj.get_text())
        remoteName = '%s%d' % (self.providerName, time.time())
        if len(opts):        
            exe = 'rclone config create ', remoteName, ' ', self.providerName, ' '.join(opts)
        else:      
            exe = 'rclone config create %s %s' % (remoteName, self.providerName)
        try:
            py2code = subprocess.check_call(exe.split(' '))
            print('py2 said:', py2code)
            if py2code  == 0:
                self.storeRemote.append([str(remoteName), str(self.providerName)])
                msg = 'Your remote has been successfully configured...'
            else:
                msg = 'Failed to configure your remote...'
            print("INFO dialog closed")
        except subprocess.CalledProcessError as e:
            msg = 'Failed to configure your remote...'
        dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, msg)
        dialog.run()
        dialog.destroy()

    def populate(self, name):
        for opt in self.listOptions:
            opt.hide()
            self.vbox.remove(opt)

        self.listOptions = []
        self.listOptionsObj = []
        self.providerName = name

        for value in self.jsonProviders:
             if str(value.Name) == name:
                for opts in value.Options:
                    hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
                    hbox.set_homogeneous(False)
                    hbox.show()
                    self.listOptions.append(hbox)
                    label = Gtk.Label()
                    label.show()
                    label.set_text(opts.Help)
                    hbox.pack_start(label, False, False, 0)
                    entry = Gtk.Entry()
                    entry.show()
                    entry.set_name(opts.Name)
                    hbox.pack_start(entry, False, False, 0)
                    self.listOptionsObj.append(entry)
                    self.frameNewBox.pack_start(hbox, False, False, 0)
                hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
                hbox.set_homogeneous(False)
                hbox.show()
                self.listOptions.append(hbox)
                button = Gtk.Button.new_with_label("Create new remote")
                button.connect("clicked", self.on_new_remote)
                hbox.pack_start(button, False, False, 0)
                button.show()
                self.frameNewBox.pack_start(hbox, False, False, 0)


    def on_name_combo_changed(self, combo):
        tree_iter = combo.get_active_iter()
        if tree_iter != None:
            model = combo.get_model()
            row_id, name = model[tree_iter][:2]
            self.populate(name)
            # print("Selected: ID=%d, name=%s" % (row_id, name))

    def boxProviders(self):
        s = subprocess.check_output(['rclone', 'config', 'providers'])
        output = s.decode("utf-8")
        self.jsonProviders = json.loads(output, object_hook=lambda d: Namespace(**d))
        self.providers_store = Gtk.ListStore(int, str)
        cpt = 0
        for value in self.jsonProviders:
            cpt = cpt + 1
            self.providers_store.append([cpt, str(value.Name)])
        name_combo = Gtk.ComboBox.new_with_model_and_entry(self.providers_store)
        name_combo.connect("changed", self.on_name_combo_changed)
        name_combo.set_entry_text_column(1)
        return name_combo

    def update_remotes_list(self):
        s = subprocess.check_output(['rclone' ,'config', 'dump'])
        output = s.decode("utf-8")
        self.jsonRemotes = json.loads(output)

    def __init__(self):
        self.update_remotes_list()
        Gtk.Window.__init__(self, title="Confih Ui Rclone")
        self.listOptions = []
        self.set_default_size(600,480)
        self.resize(600,480)
        self.set_border_width(10)
        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.vbox.show()
        self.remote()
        self.frameNewBox = self.frameBoxVertical('New remote')
        self.frameNewBox.show()
        self.name_combo = self.boxProviders()
        self.frameNewBox.pack_start(self.name_combo, False, False, 0)
        self.add(self.vbox)

    def on_list_remote_changed(self, tree_selection):
        type_remote = ''
        (model, pathlist) = tree_selection.get_selected_rows()
        for path in pathlist :
             tree_iter = model.get_iter(path)
             type_remote = model.get_value(tree_iter,1)
        item = self.providers_store.get_iter_first ()
        model = self.name_combo.get_model()
        while ( item != None ):
             if type_remote == model.get_value(item, 1):
                 self.name_combo.set_active_iter(item)
                 return
             item = self.providers_store.iter_next(item)

    def remote(self):
        self.storeRemote = Gtk.ListStore(str, str)
        self.frameModifyBox = self.frameBoxVertical('List remotes')
        self.frameModifyBox.show()
        for value in self.jsonRemotes:
            self.storeRemote.append([str(value), str(self.jsonRemotes[value]['type'])])
        self.tree = Gtk.TreeView(self.storeRemote)
        self.tree.props.activate_on_single_click = True
        self.tree_selection = self.tree.get_selection()
        self.tree_selection.connect("changed", self.on_list_remote_changed)
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn('Remote Name', renderer, text=0)
        self.tree.append_column(column)
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn('Type', renderer, text=1)
        self.tree.append_column(column)
        self.tree.show()
        self.frameModifyBox.pack_start(self.tree, False, False, 0)
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.frameModifyBox.pack_start(hbox, False, False, 0)
        hbox.show()
        button = Gtk.Button.new_with_label("Delete remote")
        button.connect("clicked", self.on_delete_remote)
        hbox.pack_start(button, False, False, 0)
        button = Gtk.Button()
        hbox.pack_start(button, False, False, 0)
        button = Gtk.Button()
        hbox.pack_start(button, False, False, 0)

win = ComboBoxWindow()
win.connect("delete-event", Gtk.main_quit)
win.show_all()
Gtk.main()
