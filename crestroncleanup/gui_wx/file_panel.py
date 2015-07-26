import os
import wx
import wx.aui
import wx.dataview
import app

from gui_wx import embedded_graphics_16 as eg
from obj_types import ObjType


class FilePanel(wx.Panel):
    """
    File Panel contains the File Note Book.
    """

    def __init__(self, *args, **kwargs):
        super(FilePanel, self).__init__(*args, **kwargs)
        self.file_notebook = FileNoteBook(self)
        sizer = wx.BoxSizer()
        sizer.Add(self.file_notebook, 1, wx.EXPAND)
        self.SetSizer(sizer)
        wx.CallAfter(self.file_notebook.SendSizeEvent)


class FileNoteBook(wx.aui.AuiNotebook):
    """
    File Note Book contains the tabbed file views.
    """

    def __init__(self, *args, **kwargs):
        super(FileNoteBook, self).__init__(*args, **kwargs)

    def add_file(self, filepath, filename):
        """
        Add a file page to the file notebook.
        :param filepath: Name of directory path containing the file.
        :param filename: Name of the file.
        """
        file_page = FilePage(filepath, filename, self)
        self.AddPage(file_page, filename)


class FilePage(wx.Panel):
    """
    File Page contains the controls to interact with the file.
    """

    TBFLAGS = (wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT)

    def __init__(self, filepath, filename, *args, **kwargs):
        """
        :param filepath: Name of directory path containing the file.
        :param filename: Name of the file.
        """
        super(FilePage, self).__init__(*args, **kwargs)

        self.overwrite = False
        self.backup = True

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(self._create_toolbar(), 0, wx.EXPAND)

        text_box = wx.TextCtrl(self, wx.ID_ANY, style=(wx.TE_MULTILINE | wx.TE_READONLY))

        sizer = wx.BoxSizer()
        sizer.Add(text_box, 1, wx.EXPAND)

        self.filename = os.path.join(filepath, filename)
        self.data = app.read_file(self.filename)

        model = FileTreeListModel(self.data.obj_dict)

        dvc = wx.dataview.DataViewCtrl(self, style=(wx.BORDER_THEME
                                                    | wx.dataview.DV_ROW_LINES
                                                    | wx.dataview.DV_VERT_RULES
                                                    | wx.dataview.DV_MULTIPLE))
        dvc.AssociateModel(model)
        tr = wx.dataview.DataViewTextRenderer()
        dvc.AppendColumn(wx.dataview.DataViewColumn('Type', tr, 0, width=80))
        dvc.AppendTextColumn('Name', 1, width=400, mode=wx.dataview.DATAVIEW_CELL_EDITABLE)
        header = self.data.get_header()

        text_box.SetValue('Program name: %s\nDealer: %s\nProgrammer: %s' %
                          (header.name, header.dealer, header.programmer))

        main_sizer.Add(dvc, 1, wx.EXPAND)
        main_sizer.Add(sizer, 1, wx.EXPAND)

        self.SetSizer(main_sizer)

    def _create_toolbar(self):
        # Draw the toolbar
        toolbar = wx.ToolBar(self, style=self.TBFLAGS)
        toolbar.SetMargins((4, 4))
        toolbar.SetToolSeparation(32)

        # Save Button
        toolbar.AddLabelTool(wx.ID_SAVE, 'Save', eg.GetBitmap_save_png(), shortHelp='Save the file')
        self.Bind(wx.EVT_TOOL, self._on_save, id=wx.ID_SAVE)

        toolbar.AddSeparator()

        # Process Button
        toolbar.AddSimpleTool(wx.ID_CONVERT, eg.GetBitmap_play_png(), shortHelpString='Process file')
        self.Bind(wx.EVT_TOOL, self._on_process, id=wx.ID_CONVERT)

        toolbar.AddSeparator()

        # Settings Button
        toolbar.AddSimpleTool(wx.ID_SETUP, eg.GetBitmap_cog_png(), shortHelpString='Change file settings')
        self.Bind(wx.EVT_TOOL, self._on_settings, id=wx.ID_SETUP)

        toolbar.AddStretchableSpace()

        # Pacman Button
        toolbar.AddSimpleTool(wx.ID_ANY, eg.GetBitmap_pacman_png(), shortHelpString='Pacman')
        self.Bind(wx.EVT_TOOL, self._on_pacman, id=wx.ID_SETUP)

        toolbar.Realize()
        return toolbar

    def _on_save(self, event):
        app.save_file(self.data, self.filename, self.overwrite, self.backup)

    def _on_settings(self, event):
        pass

    def _on_process(self, event):
        self.data.process()

    def _on_pacman(self, event):
        pass


class FileTreeListModel(wx.dataview.PyDataViewModel):
    MAPPER = {
        0: 'string',  # Object Type
        1: 'string',  # Object Name
    }

    def __init__(self, data, *args, **kwargs):
        super(FileTreeListModel, self).__init__(*args, **kwargs)
        self._data = {k: v for k, v in data.items() if
                      k not in ['Bk', 'Bw', 'CED', 'Cm', 'Cs', 'Et', 'EtU', 'FP', 'FSgntr', 'SrU']}

        self.objmapper.UseWeakRefs(False)

    def GetColumnCount(self):
        return 2

    def GetColumnType(self, col):
        return self.MAPPER[col]

    def GetChildren(self, parent, children):
        if not parent:
            for name, items in self._data.items():
                children.append(self.ObjectToItem({name: items}))
            return len(self._data)

        node = self.ItemToObject(parent)
        if isinstance(node, dict):
            for obj in node.values()[0]:
                children.append(self.ObjectToItem(obj))
            return len(node.values()[0])

        return 0

    def IsContainer(self, item):
        if not item:
            return True

        node = self.ItemToObject(item)
        return isinstance(node, dict)

    def GetParent(self, item):
        if not item:
            return wx.dataview.NullDataViewItem

        node = self.ItemToObject(item)
        if isinstance(node, dict):
            return wx.dataview.NullDataViewItem
        elif isinstance(node, ObjType):
            for name, items in self._data.items():
                if name == node.ObjTp:
                    return self.ObjectToItem({name: items})

    def GetValue(self, item, col):
        node = self.ItemToObject(item)

        if isinstance(node, dict):
            mapper = {
                0: node.values()[0][0].desc,
                1: '',
            }
            return mapper[col]

        if isinstance(node, ObjType):
            mapper = {
                0: node.id,
                1: str(node.name),
            }
            return mapper[col]

        raise RuntimeError("unknown node type")

    def GetAttr(self, item, col, attr):
        node = self.ItemToObject(item)
        if isinstance(node, dict):
            attr.SetColour('blue')
            attr.SetBold(True)
            return True
        return False
