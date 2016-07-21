from win32com.client import Dispatch
import kustom_widgets as kw
import collections
import numpy as np
import csv


class ActiveExcel(object):

    def __init__(self, sheet=None):
        self.setup_active(sheet)
        self.set_excel_constants()

    def setup_active(self, sheet=None):
        # self.live_sheet_name = sheet
        self.excel = Dispatch('Excel.Application')  # get a handle to the Excel COM object
        self.live_wb = self.excel.ActiveWorkbook  # .Add(filename)
        if sheet is None:
            self.live_ws = self.live_wb.ActiveSheet
        else:
            self.live_ws = self.live_wb.Worksheets(sheet)

    def get_sel(self):
        self.selection = self.excel.selection.Value
        return self.selection

    def put_data(self, list_like):
        address = self.excel.selection.address
        new_address = XlAddress.from_alpha(address)
        list_dims = XlAddress.from_data(list_like)
        list_dims.offset_range(new_address.start-(1, 1))
        self.live_ws.Range(list_dims.address).Value = list_like

    def paste_header_data(self, list_like, inp_address=None):
        address = inp_address
        if not inp_address:
            address = self.excel.selection.address
        new_address = XlAddress.from_alpha(address)
        list_dims = XlAddress.from_data(list_like)
        list_dims.offset_range(new_address.start-(1, 0))
        self.live_ws.Range(list_dims.address).Value = list_like

    def get_cd(self, inp_address=None):
        address = inp_address
        if not inp_address:
            inp_address = self.excel.selection.address
        address = XlAddress.from_alpha(inp_address)
        last_col = self.last_column_in_row(address.bounds[0])
        address = XlAddress.from_tuple(((address.bounds[0]), (last_col, address.bounds[1][1])))
        headers = self.live_ws.Range(address.address).Value[0]
        return headers

    def last_column_in_row(self, address):
        big_num = self.live_ws.Cells(1, self.live_ws.Columns.Count).End(self.xl_cons['xlToRight']).Column
        max_gap = 5
        start_address = XlAddress.from_tuple((address, (big_num, address[1])))
        row_data = self.live_ws.Range(start_address.address).Value
        counter = 0
        for cell in enumerate(row_data[0]):
            if cell[1] is None:
                counter += 1
            else:
                counter = 0
            if counter >= max_gap:
                break
        return cell[0] - max_gap + 2

    def set_excel_constants(self):
        self.xl_cons = {
                        'xlToLeft': 1,
                        'xlToRight': 2,
                        'xlUp': 3,
                        'xlDown': 4,
                        'xlThick': 4,
                        'xlThin': 2,
                        'xlEdgeBottom': 9,
                        }

    def write_csv(self, list_of_lists, filename):
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(list_of_lists)

    def read_csv(self, filename):
        return_dict = collections.OrderedDict()
        with open(filename, 'r') as f:
            reader = csv.reader(f)
            first_row = True
            for row in reader:
                if first_row:
                    for header in row:
                        return_dict[header] = []
                    first_row = False
                    header_list = list(return_dict)
                else:
                    for i in range(len(row)):
                        return_dict[header_list[i]].append(row[i])
        return return_dict







class XlAddress(object):

    def __init__(self):
        pass

    @classmethod
    def from_alpha(cls, address):
        self = cls()
        self.address = address.replace('$', '')
        self.alpha_to_bounds()
        return self

    @classmethod
    # This needs fixing
    def from_data(cls, dlist):
        self = cls()
        try:
            self.row_count = len(dlist)
            self.column_count = len(dlist[0])
        except TypeError:
            try:
                self.row_count = 1
                self.column_count = len(dlist)
            except TypeError:
                    self.row_count = 1
                    self.column_count = 1
        self.address = ('A1:' + (kw.num2alpha(self.column_count).upper()) + str(self.row_count))
        self.alpha_to_bounds()
        return self

    @classmethod
    def from_tuple(cls, double_tuple):
        self = cls()
        self.bounds = double_tuple
        self.bounds_to_points()
        self.bounds_to_alpha()
        return self

    def alpha_to_bounds(self):
        slash_pos = self.address.find(':')
        if slash_pos == -1:
            self.address += ':' + self.address
            slash_pos = self.address.find(':')
        address_tuple = self.address[:slash_pos], self.address[slash_pos+1:]
        self.bounds = []
        for a in address_tuple:
            alpha = ''
            number = ''
            for letter in a:
                if letter.isnumeric():
                    number += letter
                else:
                    alpha += str(letter)
            self.bounds.append((int(kw.alpha2num(alpha)), int(number)))
        self.bounds = np.array(self.bounds)
        self.bounds_to_points()

    def bounds_to_points(self):
        self.address_numeric = self.bounds
        self.start = self.bounds[0]
        self.end = self.bounds[1]
        self.column_count = self.end[0] - self.start[0] + 1
        self.row_count = self.end[1] - self.start[1] + 1

    def offset_range(self, row_col_tuple):
        rc_offset = np.array(row_col_tuple)
        self.bounds[0] = self.bounds[0] + rc_offset
        self.bounds[0][self.bounds[0] < 1] = 1
        self.bounds[1] = self.bounds[0] + (self.column_count-1, self.row_count-1)
        self.bounds_to_points()
        self.bounds_to_alpha()

    def bounds_to_alpha(self):
        self.address = ((kw.num2alpha(self.start[0]).upper()) + str(self.start[1]) +
                        ':' + (kw.num2alpha(self.end[0]).upper()) + str(self.end[1]))
