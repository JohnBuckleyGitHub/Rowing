import shutil
import copy
from os import path
from send2trash import send2trash
from PyQt4 import QtCore
from PyQt4 import QtGui
import collections
import csv
from scipy import interpolate
import numpy as np
# import sys
# import math
# sys.path.insert(0, 'C:/Python Files/pythonlibs')
# import kustomDBtools


    ###############################################################################
    #Contains status_label_class, qsettings_handler, and brushstyle
    ###############################################################################


    ##############################################################################
    # Status bar
    #
    # Requires a scrolled window with an area called status_label
    # Best if inherited upon window declaration class MyWindow(QtGui.QMainWindow,  kustomWidgets.status_label_class, ...)
    #
    ##############################################################################

class status_label_class(object):
    def __init__(self):
        pass
        # self.status_label = window.status_label

    def statusbar_add(self, new_text, special_text=False):
        html_ins = ''
        if special_text is False:
            html_ins = special_text
        current_text = self.status_label.text()
        full_text = "<p><" + html_ins + ">" + new_text + "</" + html_ins + "></p>" + current_text
        line_count = full_text.count('</p>')
        if line_count > 100:
            last_n = full_text.rfind('</p>')
            full_text = full_text[:last_n]
        self.status_label.setText(full_text)

    ##############################################################################
    # QSettings handling - save, default, delete
    #
    # Requires a scrolled window with an area called status_label
    # Initiated as a new object and window refers to the active window
    #
    ##############################################################################


class qsettings_handler(object):

    from PyQt4 import QtCore
    from PyQt4 import QtGui

    def __init__(self, window, prefix_name, default_setting_name):
        self.window = window
        self.view_settings_comboBox = window.view_settings_comboBox
        self.qsettings_prefix_name = prefix_name  # "DB Admin"
        self.qsettings_company = "Your logo here"
        self.qsettings_name = default_setting_name  # "column_view"
        self.qt_settings = QtCore.QSettings(self.qsettings_company, self.qsettings_name)

    def column_order_store(self):
        self.qt_settings.setValue(self.qsettings_name, self.window.DB_tableWidget.horizontalHeader().saveState())

    def load_view_settings(self):
        self.view_settings_comboBox.clear()
        db_obj = self.config_qsetting()
        saved_views = ['Current']
        actions = ['Save Current', 'Delete View']
        for entry in db_obj.entries:
            first_comma = entry['Full_Name'].find(",")
            new_view = entry['Full_Name'][first_comma+1:]
            saved_views.append(new_view)
        saved_views += actions
        self.view_settings_comboBox.addItems(saved_views)
        self.delete_view = False

    def change_view_settings(self):
        combo_box = self.view_settings_comboBox
        current_selection = combo_box.currentText()
        db_obj = self.config_qsetting()
        if self.delete_view is False:
            if current_selection == 'Current':
                return
            elif current_selection == 'Save Current':
                all_box_items = [combo_box.itemText(i) for i in range(combo_box.count())]
                new_view_name = 'Save Current'  # to keep while loop going
                while new_view_name in all_box_items:
                    new_view_name, ok_or_cancel = QtGui.QInputDialog.getText(self.window, 'New View Name',
                                                                             'Enter a name for the new saved view:')
                    if new_view_name in all_box_items or new_view_name == '':
                        self.window.statusbar_add('View name ' + new_view_name + ' already exists')
                if ok_or_cancel is False:
                    self.load_view_settings()
                    self.window.statusbar_add("Save view exited")
                    return
                if new_view_name == "Default Replace":
                    new_view_name = "Default"
                insert_dict = {}
                insert_dict['Full_Name'] = self.qsettings_prefix_name + ',' + new_view_name
                insert_dict['Company'] = self.qsettings_company
                insert_dict['Qbyte_String'] = self.window.DB_tableWidget.horizontalHeader().saveState()
                statustext = db_obj.insert_row(insert_dict)
                if statustext:
                    self.window.statusbar_add(str(statustext))
                self.load_view_settings()
            elif current_selection == 'Delete View':
                self.delete_view = True
                self.window.statusbar_add("Delete view mode: Select a view to delete", special_text='b')
                return
            elif (current_selection != 'Current' and current_selection != 'Save Current' and
                  current_selection != 'Delete Current'):
                db_obj.select_all()
                found = False
                for entry in db_obj.entries:
                    first_comma = entry['Full_Name'].find(",")
                    new_view = entry['Full_Name'][first_comma+1:]
                    if new_view == current_selection:
                        self.window.statusbar_add(current_selection + " view retrieved from config.db")
                        found = True
                        self.qt_settings.setValue(self.qsettings_name, entry['Qbyte_String'])
                        self.window.DB_tableWidget.horizontalHeader().restoreState(self.qt_settings.value(self.qsettings_name)) #reset columns
                if not found:
                    self.window.statusbar_add(current_selection + " not found in config.db, no change made.")
                self.load_view_settings()
                self.window.refresh_db_table()
        elif self.delete_view == True:
            undeletable = ['Current', 'Save Current', 'Delete View', 'Default']
            if current_selection not in undeletable:
                delete_box = QtGui.QMessageBox()
                delete_box.setText("Do you want to delete view " + current_selection)
                delete_box.setStandardButtons(delete_box.Ok | delete_box.Cancel)
                answer = delete_box.exec()
                if answer == 0x00000400: # 0x00000400 is OK see - http://qt-project.org/doc/qt-4.8/qmessagebox.html#StandardButton-enum
                    db_obj.remove_row('Full_Name', self.qsettings_prefix_name + ',' + current_selection)
                    self.window.statusbar_add(current_selection + " removed from config.db")
            self.delete_view = False
            self.window.statusbar_add("Delete view mode: exited", special_text='b')
            self.load_view_settings()

    def config_qsetting(self):
        db_name = "config.db"
        conn_string = db_name
        default_table = "Qsettings_External"
        select_default = ("WHERE Company='" + self.qsettings_company + "' AND Full_Name LIKE '" +
            self.qsettings_prefix_name + "%'")
        # config_db_obj = kustomDBtools.db_obj(conn_string, default_table, select_default)
        config_db_obj.select_all()
        return(config_db_obj)

    #######################################
    # brushsyle contains brushestyles with predefined colors
    #######################################


class brushstyle(object):

    def __init__(self):
        self.red = BrushyBrush((255, 189, 189))
        self.green = BrushyBrush((189, 255, 189))
        self.blue = BrushyBrush((189, 189, 255))
        self.lred = BrushyBrush((255, 219, 219))
        self.lgreen = BrushyBrush((219, 255, 219))
        self.lblue = BrushyBrush((219, 219, 255))
        self.dred = BrushyBrush((255, 119, 119))
        self.dgreen = BrushyBrush((119, 255, 119))
        self.dblue = BrushyBrush((119, 119, 255))
        self.grey = BrushyBrush((80, 80, 80))
        self.nobrush = BrushyBrush((255, 255, 255))


class BrushyBrush(QtGui.QBrush):

    def __init__(self, rgb):
        r, g, b = rgb
        super().__init__(QtGui.QColor(r, g, b))
        self.setStyle(QtCore.Qt.SolidPattern)

    def brush_to_rgb(self):
        return (self.color().red(), self.color().green(), self.color().blue())

    def brush_to_rgbhex(self):
            rgb_tuple = self.brush_to_rgb()
            return '#%02x%02x%02x' % rgb_tuple

    #######################################
    # Misc
    #######################################


class file_handler(object):

    def __init__(self):
        pass

    @classmethod
    def from_file(cls, bare_filename, dpath=None):
        self = cls()
        self.basename = bare_filename
        self.sort_extensions()
        if dpath:
            self.add_path(dpath)
            self.fullpath = self.path_sl + self.basename
        else:
            self.fullpath = self.basename
        return self

    @classmethod
    def from_fullpath(cls, fullpath):
        self = cls()
        self.fullpath = self.fix_slash(fullpath)
        self.basename = path.basename(fullpath)
        rawpath = fullpath[:-len(self.basename)-1]
        self.add_path(rawpath)
        self.sort_extensions()
        return self

    def sort_extensions(self):
        dot_place = self.basename.rfind('.')
        self.file_ext = self.basename[dot_place:]
        self.file_no_ext = self.basename[:dot_place]

    def add_path(self, path):
        path = self.fix_slash(path)
        self.path_sl = self.add_t_slash(path)
        self.path_nosl = self.path_sl[:-2]
        self.fullpath = self.path_sl + self.basename

    def duplicate(self, name_ext):
        new_fullpath = self.path_sl + self.file_no_ext + name_ext + self.file_ext
        shutil.copy2(self.fullpath, new_fullpath)
        return file_handler.from_fullpath(new_fullpath)

    def delete(self):
        send2trash(self.fullpath)
        for attrib in self.__dict__.items():
            setattr(self, attrib[0], None)

    def fix_slash(self, init_str):
        return init_str.replace('/', '\\')

    def add_t_slash(self, init_str):
        if init_str[-1:] != "\\":
            return init_str + "\\"
        return init_str


def dir_clean(init_str):
    init_str = init_str.replace('/', '\\')
    if init_str[-1:] != "\\":
        return init_str + "\\"
    return init_str


def zeronater(number, place_count):
    if number < 1:
        output_string = ''
        for i in range(place_count):
            output_string += '0'
        return output_string
    # places = int(math.log(number)/math.log(10) + 1)
    places = len(str(number))
    output_string = str(int(number))
    for i in range(place_count - places):
        output_string = '0' + output_string
    return output_string


def letter_increment(letters, increment):
    init_value = alpha2num(letters.lower())
    new_letters = num2alpha(init_value + increment)
    if letters.isupper():
        new_letters = new_letters.upper()
    return new_letters


def alpha2num(letters):
    letters = letters.lower()
    abet = alphabet()
    base = len(abet)
    alpha_places = len(letters)
    total = 0
    for place in range(alpha_places):
        cur_letter = letters[alpha_places - place - 1]
        loc = abet.find(cur_letter) + 1
        total += (loc*(base**place))
    return total


def num2alpha(num):
    numerals = alphabet()
    base = len(numerals)
    s = ''
    if num == 0:
        return 0
    num -= 1  # since 0 is 0 and A is 1
    for i in range(20):
        s = numerals[int(num % base)] + s
        num = num / base
        if num < 1:
            break
        num -= 1
    return s


def alphabet():
    return 'abcdefghijklmnopqrstuvwxyz'


def clean_number(number_string):
    clean_num_str = ''
    for char in number_string:
            try:
                clean_num_str += str(int(char))
            except:
                pass
    if len(clean_num_str) > 0:
        return int(clean_num_str)
    return 0


def png_id_str(string_list, id_str, char_places, min_number=1, zeronater_places=0):
    number_list = []
    for item in string_list:
        place = item.find(id_str)
        if place < 0:
            continue
        number_string = item[place + len(id_str):place + len(id_str) + char_places]
        print(number_string)
        number_list.append(int(clean_number(number_string)))
    print(number_list)
    max_number = 10**(zeronater_places+1)
    if min_number > max_number:
        max_number = min_number
    for i in range(min_number, max_number):
        if i not in number_list:
            break
    if zeronater_places > 0:
        return zeronater(i, zeronater_places)
    return str(i)


def increment_dict(ndict, num, value):
    if num in ndict:
        num2 = num + 1
        increment_dict(ndict, num2, ndict[num])
    ndict[num] = value
    return ndict


def select_data(line, precursor=None, postcursor=None, start_find_str=None, start_find_num=None):
    if start_find_num:
        start_find = start_find_num
    elif start_find_str:
        start_find = line.find(start_find_str)
    else:
        start_find = 0
    if precursor:
        precursor_pos = line.find(precursor, start_find) + len(precursor)
    else:
        precursor_pos = None
    if postcursor:
        postcursor_pos = line.find(postcursor, precursor_pos)
    else:
        postcursor_pos = None
    return line[precursor_pos:postcursor_pos]


def pythag(x, y):
    return (x**2 + y**2)**0.5


def write_csv(list_of_lists, filename):
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(list_of_lists)


def read_csv_to_dict(filename):
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


def function_from_csv(filename, x_param, y_param):
    csv_dict = read_csv_to_dict(filename)
    x = csv_dict[x_param]
    y = csv_dict[y_param]
    return interpolate.interp1d(np.array(x, 'float'), np.array(y, 'float'))
