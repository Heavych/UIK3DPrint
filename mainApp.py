import sys
import os
from mainWin import Ui_MainWindow
import loginDialog, learnDialog, addDialog, aboutDialog, examDialog
from PyQt5 import QtWidgets
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QIcon, QPixmap, QMovie, QDesktopServices
from PyQt5.QtWidgets import QApplication, QFileDialog, QDialog, QMainWindow, QTableWidgetItem
import sqlite3
import stl
from stl import mesh
import numpy
from mpl_toolkits import mplot3d
from matplotlib import pyplot


progname = os.path.basename(sys.argv[0])
progversion = "0.1"

conn = sqlite3.connect('uikDB.db')
curs = conn.cursor()
theme_vkr = 'УИК для 3D-печати полимерных изделий различной конфигурации'


class MainApp(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MainApp, self).__init__(parent)
        self.init_ui()
        self.setWindowTitle(theme_vkr)  # Название программы
        self.setWindowIcon(QIcon('img/icon.png'))  # Иконка программы
        self.comboBox.addItems(["ВСЕ", "БЫТОВЫЕ", "ПРОФЕССИОНАЛЬНЫЕ", "ЮВЕЛИРНЫЕ"])


    def mesh_dimensions(self, obj):
        minx, maxx, miny, maxy, minz, maxz = self.find_mins_maxs(obj)
        meshx = maxx - minx
        meshy = maxy - miny
        meshz = maxz - minz
        mesh_dimension = [meshx, meshy, meshz]
        self.spinBox_ModelSizeX.setProperty("value", int(meshx))
        self.spinBox_ModelSizeY.setProperty("value", int(meshy))
        self.spinBox_ModelSizeZ.setProperty("value", int(meshz))
        return mesh_dimension

    def find_mins_maxs(self, obj):
        minx = maxx = miny = maxy = minz = maxz = None

        for p in obj.points:
            # p contains (x, y, z)
            if minx is None:
                minx = p[stl.Dimension.X]
                maxx = p[stl.Dimension.X]
                miny = p[stl.Dimension.Y]
                maxy = p[stl.Dimension.Y]
                minz = p[stl.Dimension.Z]
                maxz = p[stl.Dimension.Z]
            else:
                maxx = max(p[stl.Dimension.X], maxx)
                minx = min(p[stl.Dimension.X], minx)
                maxy = max(p[stl.Dimension.Y], maxy)
                miny = min(p[stl.Dimension.Y], miny)
                maxz = max(p[stl.Dimension.Z], maxz)
                minz = min(p[stl.Dimension.Z], minz)
        return minx, maxx, miny, maxy, minz, maxz

    def link(self, linkStr):
        QDesktopServices.openUrl(QUrl(linkStr))

    def init_ui(self):
        self.setupUi(self)
        self.load_database()
        self.label_PrinterImage.setPixmap(QPixmap("img/printers/default.jpg"))
        self.label_Image.setPixmap(QPixmap("img/main_g.jpg"))
        self.label_LogAdmin.hide()
        self.pushButtonAdd.hide()
        self.pushButtonDel.hide()
        self.pushButtonExam.clicked.connect(self.show_exam_dialog)

        self.pushButton_ResultNext.hide()

        if flagLoginAdmin:
            self.setWindowTitle(theme_vkr + " " + "[Режим администратора]")
            self.pushButtonAdd.show()
            self.pushButtonDel.show()
            self.label_LogAdmin.show()
            self.pushButtonAdd.clicked.connect(self.show_add_dialog)
            self.pushButtonDel.clicked.connect(self.delete_data)
            self.pushButtonGo.clicked.connect(self.result_start)
            self.pushButtonFile.clicked.connect(self.show_file_dialog)
            # self.pushButtonGo.setShortcut('Return')  #
            self.label_LogAdmin.setText("Режим администратора")
            self.statusBar().showMessage('Готово')
            self.show()

        else:
            # self.pushButton_Next.clicked.connect(self.ShowLearnDialog)
            self.show_learn_dialog()
            self.pushButtonGo.clicked.connect(self.result_start)
            self.pushButtonAdd.hide()
            self.pushButtonDel.hide()
            self.label_LogAdmin.hide()
            self.statusBar().hide()

        self.action_Open.triggered.connect(self.show_file_dialog)
        self.action_Learn.triggered.connect(self.show_learn_dialog)
        self.action_Exam.triggered.connect(self.show_exam_dialog)
        self.action_About.triggered.connect(self.show_about_dialog)
        self.pushButtonFile.clicked.connect(self.show_file_dialog)

    def show_learn_dialog(self):
        self.adding = LearnDialog()
        self.adding.exec_()
        self.show()

    def show_exam_dialog(self):
        self.adding = ExamDialog()
        self.adding.exec_()

    def show_add_dialog(self):
        self.adding = AddDialog()
        self.adding.pushButtonInsert.clicked.connect(self.add_data)
        totalCount = int(self.tableWidget.rowCount()) + 1
        self.adding.spinBox_PrinterID.setMinimum(totalCount)

        curs = conn.cursor()
        search_query = """SELECT COUNT(*) FROM  Manufacturers"""
        curs.execute(search_query)
        man_count = curs.fetchall()
        conn.commit()
        max_man_count = man_count[0][0]
        self.adding.spinBox_ManufacturerID.setMaximum(max_man_count)
        self.adding.exec_()

    def show_about_dialog(self):
        self.adding = AboutDialog()
        self.adding.exec_()

    def show_file_dialog(self):
        try:
            fname = QFileDialog.getOpenFileName(self, 'Open file', '', "STL (*.stl)")[0]
            your_mesh = mesh.Mesh.from_file(fname)
        except Exception as error:
            VERTICE_COUNT = 100
            data = numpy.zeros(VERTICE_COUNT, dtype=mesh.Mesh.dtype)
            your_mesh = mesh.Mesh(data, remove_empty_areas=False)
            # The mesh normals (calculated automatically)
            your_mesh.normals
            # The mesh vectors
            your_mesh.v0, your_mesh.v1, your_mesh.v2
            # Accessing individual points (concatenation of v0, v1 and v2 in triplets)
            assert (your_mesh.points[0][0:3] == your_mesh.v0[0]).all()
            assert (your_mesh.points[0][3:6] == your_mesh.v1[0]).all()
            assert (your_mesh.points[0][6:9] == your_mesh.v2[0]).all()
            assert (your_mesh.points[1][0:3] == your_mesh.v0[1]).all()

        self.mesh_dimensions(your_mesh)
        figure = pyplot.figure(figsize=(02.00, 02.00))
        axes = mplot3d.Axes3D(figure)
        axes.add_collection3d(mplot3d.art3d.Poly3DCollection(your_mesh.vectors))
        scale = your_mesh.points.flatten(-1)
        axes.auto_scale_xyz(scale, scale, scale)
        figure.savefig('foo.png')
        #self.label_Image.setPixmap(QPixmap("foo.png"))


    def add_data(self):
        try:
            add_printer_id = self.adding.spinBox_PrinterID.value()
            add_model = self.adding.lineEdit_Model.text()
            add_technology_id = self.adding.spinBox_TechnologyID.value()
            add_heads_print = self.adding.lineEdit_HeadsPrint.text()
            add_layer_height = self.adding.lineEdit_LayerHeight.text()
            add_manufacturer_id = self.adding.spinBox_ManufacturerID.value()
            add_extra = self.adding.lineEdit_Extra.text()
            add_workspace_x = self.adding.lineEdit_WorkspaceX.text()
            add_workspace_y = self.adding.lineEdit_WorkspaceY.text()
            add_workspace_z = self.adding.lineEdit_WorkspaceZ.text()
            add_extruder_temp = self.adding.spinBox_ExtruderTemp.value()
            add_speed_print = self.adding.lineEdit_SpeedPrint.text()
            add_price = self.adding.lineEdit_Price.text()
            add_image = self.adding.lineEdit_Image.text()
            add_category_id = self.adding.spinBox_CategoryID.value()

            # tAdd_PrinterID = int(self.tableWidget.rowCount()) + 1

            query = "INSERT INTO Printers (PrinterID, Model, TechnologyID, HeadsPrint, LayerHeight, ManufacturerID, " \
                    "Extra, WorkspaceX, WorkspaceY, WorkspaceZ, ExtruderTemp, SpeedPrint, Price, Image, СategoryID) " \
                    "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);"

            curs.execute(query, (add_printer_id, add_model, add_technology_id, add_heads_print, add_layer_height,
                                 add_manufacturer_id, add_extra, add_workspace_x, add_workspace_y, add_workspace_z,
                                 add_extruder_temp, add_speed_print, add_price, add_image, add_category_id))
            conn.commit()
            print('ADD DONE')
            self.load_database()
        except Exception as error:
            print(error)
            QtWidgets.QMessageBox.warning(self, theme_vkr, "Ошибка")

    def delete_data(self):
        try:
            content = 'SELECT * FROM Printers'
            res = curs.execute(content)
            for row in enumerate(res):
                if row[0] == self.tableWidget.currentRow():
                    data = row[1]
                    query = "DELETE FROM Printers WHERE PrinterID=? AND Model=? AND TechnologyID=? AND HeadsPrint=? " \
                            "AND LayerHeight=? AND ManufacturerID=? AND Extra=? AND WorkspaceX=? AND WorkspaceY=? " \
                            "AND WorkspaceZ=? AND ExtruderTemp=? AND SpeedPrint=? AND Price=? AND Image=? " \
                            "AND СategoryID=?"
                    curs.execute(query, (
                    data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7], data[8], data[9], data[10], data[11],
                    data[12], data[13], data[14]))
                    conn.commit()

                    self.load_database()
        except Exception as error:
            print(error)
            QtWidgets.QMessageBox.warning(self, theme_vkr, 'Выберите строку для удаления')

    def load_database(self):
        while self.tableWidget.rowCount() > 0:
            self.tableWidget.removeRow(0)
        content = """SELECT  Manufacturers.ManufacturerName, Printers.Model, Technology.TechnologyName, 
                        Printers.LayerHeight, Printers.HeadsPrint, Printers.SpeedPrint, Printers.WorkspaceX,  
                        Printers.WorkspaceY , Printers.WorkspaceZ, Printers.Extra, Printers.Price, Manufacturers.Country
                        FROM Printers 
                        INNER JOIN Technology ON Printers.TechnologyID = Technology.TechnologyID
                        INNER JOIN Manufacturers ON Printers.ManufacturerID = Manufacturers.ManufacturerID
                        INNER JOIN Categories ON Printers.СategoryID = Categories.СategoryID;"""

        res = curs.execute(content)
        for row_index, row_data in enumerate(res):
            self.tableWidget.insertRow(row_index)
            for column_index, column_data in enumerate(row_data):
                self.tableWidget.setItem(row_index, column_index, QTableWidgetItem(str(column_data)))

        self.label_total.setText("3D принтеров в базе данных: " + str(self.tableWidget.rowCount()))

        #if flagLoginAdmin == 0:
            #self.tableWidget.setColumnHidden(0, True)
        return

    def result_start(self):  # ВХОДНЫЕ ПАРАМЕТРЫ [РАЗМЕР, ЭКСТРУДЕР, !МАТЕРИАЛ!, ТОЧНОСТЬ]
        self.label_Image.setPixmap(QPixmap("img/main_in.jpg"))
        global select_printer
        global in_extruder
        global in_lh
        global in_tech
        global in_temp
        global min_cost
        global combo_text
        min_cost = 100000
        combo_text = str(self.comboBox.currentText())

        in_model_size_x = self.spinBox_ModelSizeX.value()
        in_model_size_y = self.spinBox_ModelSizeY.value()
        in_model_size_z = self.spinBox_ModelSizeZ.value()
        in_lh = self.doubleSpinBox.value()
        in_extruder = self.spinBox.value()
        if combo_text == "ВСЕ":
            self.search_printers_all(in_model_size_x, in_model_size_y, in_model_size_z, in_extruder, in_lh)

        if combo_text == "БЫТОВЫЕ":
            in_tech = 1
            self.search_printers_home(in_model_size_x, in_model_size_y, in_model_size_z, in_extruder, in_lh, in_tech, min_cost)

        if combo_text == "ПРОФЕССИОНАЛЬНЫЕ":
            self.search_printers_pro(in_model_size_x, in_model_size_y, in_model_size_z, in_extruder, in_lh, min_cost)

        if combo_text == "ЮВЕЛИРНЫЕ":
            in_tech = 2
            self.search_printers_jewelry(in_model_size_x, in_model_size_y, in_model_size_z, in_extruder, in_lh, in_tech)

    def selection_change(self, i):
        self.listWidget_Settings.clear()
        material_current = self.comboBox_Material.currentText()
        material_id_current = self.comboBox_Material.count()
        text_for_temp = "Рекомендуемая температура \nэкструдера для: "
        temp_c = " ℃"

        for count in range(material_id_current):
            self.comboBox_Material.itemText(count)
            self.listWidget_Settings.clear()

        temp_cur = row_mat[i][3]
        temp_cur_1 = temp_cur - 10
        temp_cur_2 = temp_cur + 10
        self.listWidget_Settings.addItem(
            text_for_temp + material_current + ": \nот " + str(temp_cur_1) + temp_c + " - до " + str(temp_cur_2) + temp_c)
        self.listWidget_Settings.addItem("Оптимальная температура:\n " + str(temp_cur) + temp_c)

    def search_printers_all(self, work_space_x, work_space_y, work_space_z, heads_print, in_lh):
        try:
            curs = conn.cursor()
            searchQuery = """SELECT * FROM Printers WHERE WorkspaceX>? AND WorkspaceY>? AND WorkspaceZ>? AND HeadsPrint=? 
            AND LayerHeight<=? ORDER BY Price ASC """
            curs.execute(searchQuery, (work_space_x, work_space_y, work_space_z, heads_print, in_lh))
            row = curs.fetchall()
            conn.commit()
            #print(row)
            #for varIter in range(row.__len__()):
                #print(varIter)
            var_iter = 0
            curs_2 = conn.cursor()
            search_query_2 = """SELECT * FROM Manufacturers Where ManufacturerID=?"""
            curs_2.execute(search_query_2, (row[var_iter][5],))
            row_2 = curs_2.fetchall()
            conn.commit()

            curs_3 = conn.cursor()
            search_query_3 = """SELECT * FROM Technology Where TechnologyID=?"""
            curs_3.execute(search_query_3, (row[var_iter][2],))
            row_3 = curs_3.fetchall()
            conn.commit()

            self.display_result_info(row, row_2, row_3)
            self.set_material(row)


        except Exception:
            self.notSearch()

    def display_result_info(self, res_row, res_row_2, res_row_3):
        #print(res_row)
        #var_iter = 0  # Выводить только первый результат как самый недорогой
        row_len = res_row.__len__()
        var_iter = 0

        result_data_id = res_row[var_iter][0]  # id подходящего принтера
        result_data_model = res_row[var_iter][1]  # Модель подходящего принтера
        result_data_tech = res_row[var_iter][2]  # Технология (1 = FDM 2 SLA) подходящего принтера
        result_data_extruder = res_row[var_iter][3]  # Количество экструдеров подходящего принтера
        result_data_layer_height = res_row[var_iter][4]  # Высота слоя подходящего принтера
        result_data_manufacturer = res_row[var_iter][5]  # Производитель подходящего принтера
        result_data_extra = res_row[var_iter][6]  # Дополнительные особенности подходящего принтера
        result_data_wx = res_row[var_iter][7]  # x подходящего принтера
        result_data_wy = res_row[var_iter][8]  # y подходящего принтера
        result_data_wz = res_row[var_iter][9]  # z подходящего принтера
        result_data_extruder_temp = res_row[var_iter][10]  # Температура материала подходящего принтера
        result_data_speed = res_row[var_iter][11]  # Скорость подходящего принтера
        result_data_price = res_row[var_iter][12]  # Цена подходящего принтера
        result_data_image = res_row[var_iter][13]  # Имя изображения.jpg подходящего принтера

        result_manufacturer = res_row_2[0][1]
        result_manufacturer_country = res_row_2[0][2]
        result_manufacturer_website = res_row_2[0][3]

        result_technology = res_row_3[0][1]


        self.label_ResultPrinterName.setText(str(result_manufacturer) + " " + str(result_data_model) + " (" + str(result_manufacturer_country) + ") ")

        self.listWidget_Results.clear()
        self.listWidget_Results.addItem("Технология: " + str(result_technology))
        self.listWidget_Results.addItem("Рабочая область: " + str(result_data_wx) + "x" + str(result_data_wy) + "x" + str(result_data_wz) + " ")
        self.listWidget_Results.addItem("Высота слоя: " + str(result_data_layer_height) + " мм")
        self.listWidget_Results.addItem("Скорость печати: " + str(result_data_speed) + " мм/с")
        self.listWidget_Results.addItem("Стоимость: " + str(result_data_price) + " руб.")

        self.label_PrinterImage.setPixmap(QPixmap("img/printers/" + result_data_image))

        self.label_Link.linkActivated.connect(self.link)
        manufacturerLink = '<a href=\"http://www.' + result_manufacturer_website + '/\">' + result_manufacturer_website + '</a>'
        self.label_Link.setText(manufacturerLink)
        self.listWidget_Extra.clear()
        self.listWidget_Extra.addItem(result_data_extra)

        self.statusBar().showMessage("Выполнение запроса: успешно")

    def set_material(self, row):
        rdt = row[0][2]
        in_temp = row[0][10]
        if rdt == 1:
            curs = conn.cursor()
            search_query = """SELECT * FROM Materials WHERE MaterialTemp<=? ORDER BY MaterialTemp ASC"""
            curs.execute(search_query, (in_temp,))
            global row_mat
            row_mat = curs.fetchall()
            conn.commit()

            materials_list_name = [i[1] for i in row_mat]
            self.listWidget_Settings.clear()
            self.comboBox_Material.clear()
            self.comboBox_Material.show()
            self.label_Material.setText("Материал")
            self.comboBox_Material.addItems(materials_list_name)
            self.comboBox_Material.activated.connect(self.selection_change)

        else:
            self.listWidget_Settings.clear()
            self.comboBox_Material.hide()
            self.label_Material.setText("Фотополимерная смола")
            # self.comboBox_Material.addItem("Фотополимерная смола")
            self.listWidget_Settings.addItem(
                "Фотополимерные смолы \nв основном разрабатываются \nпод конкретные установки")

    def not_found(self):
        warningMessage = "Не найдено, измените входные параметры"
        self.statusBar().showMessage(warningMessage)

        self.label_Image.setPixmap(QPixmap("img/main_g.jpg"))
        self.label_PrinterImage.setPixmap(QPixmap("img/printers/default.jpg"))
        self.listWidget_Results.clear()
        self.listWidget_Extra.clear()
        self.listWidget_Settings.clear()
        self.label_ResultPrinterName.setText("3D принтер")
        self.label_Link.clear()
        QtWidgets.QMessageBox.warning(self, theme_vkr, warningMessage)


class LoginDialog(QDialog, loginDialog.Ui_Dialog):  # Подключаем файл с ui
    def __init__(self, parent=None):
        super(LoginDialog, self).__init__(parent)
        self.setupUi(self)

        self.label.setPixmap(QPixmap("img/icon.png"))
        self.pushButton_Login.clicked.connect(self.handle_login)
        self.pushButton_User.clicked.connect(self.handle_login_user)
        # self.pushButton_User.clicked.connect(self.handleLoginUser)

    def handle_login(self):  # Функция авторизации

        curs = conn.cursor()
        curs.execute("""SELECT * FROM Users""")
        usr_row = curs.fetchone()
        conn.commit()

        if (self.lineEdit_Login.text() == usr_row[1] and self.lineEdit_Password.text() == usr_row[2]):
            global flagLoginAdmin
            flagLoginAdmin = True
            self.accept()
        else:
            QtWidgets.QMessageBox.warning(
                self, theme_vkr, 'Неправильный логин или пароль!')

    def handle_login_user(self):  # Вход пользователя
        global flagLoginAdmin
        flagLoginAdmin = False

        self.accept()


class LearnDialog(QDialog, learnDialog.Ui_Dialog):
    def __init__(self, parent=None):
        super(LearnDialog, self).__init__(parent)
        self.setupUi(self)
        self.learning_step_1()

    def learning_step_1(self):
        self.tittle = "Исследование 3D печати"
        self.setWindowTitle(self.tittle + " - начало")
        self.label.clear()
        self.label_2.clear()
        self.pushButton_Skip.clicked.connect(self.close)
        self.pushButton_Back.hide()
        self.pushButton_Next.setText("Далее")
        self.pushButton_Next.clicked.connect(self.learning_step_2)
        self.label_infoStepCount.setText("Начало")
        self.label.setPixmap(QPixmap("img/learn/slide1/slide1.png").scaledToWidth(940))
        self.label_2.show()
        self.label.setFixedHeight(440)
        movie1 = QMovie("img/learn/slide1/fdm_1.gif")
        self.label_2.setMovie(movie1)
        movie1.start()

        self.label_3.show()
        movie2 = QMovie("img/learn/slide1/sla_2.gif")
        self.label_3.setMovie(movie2)
        movie2.start()

    def learning_step_2(self):
        self.setWindowTitle(self.tittle + " - шаг 2")
        self.label.clear()
        self.label_2.clear()
        self.label_3.clear()
        self.label_2.show()
        self.label_3.show()
        self.label_infoStepCount.setText("Шаг 2")
        self.pushButton_Back.show()
        self.pushButton_Back.clicked.connect(self.learning_step_1)
        self.pushButton_Next.setText("Далее")
        self.pushButton_Next.clicked.connect(self.learning_step_3)
        self.label.setPixmap(QPixmap("img/learn/slide2/slide2.png").scaledToWidth(940))

        self.label.setFixedHeight(440)
        self.label_2.setFixedHeight(240)
        self.label_3.setFixedHeight(240)

        movie2 = QMovie("img/learn/slide2/fdm_model_2.gif")
        self.label_2.setMovie(movie2)
        movie2.start()

        movie3 = QMovie("img/learn/slide2/sla_model_2.gif")
        self.label_3.setMovie(movie3)
        movie3.start()

    def learning_step_3(self):
        self.setWindowTitle(self.tittle + " - шаг 3")
        self.label.clear()
        self.label_2.clear()
        self.label_3.clear()
        self.label_infoStepCount.setText("Шаг 3")
        self.pushButton_Back.clicked.connect(self.learning_step_2)
        self.pushButton_Next.setText("Далее")
        self.pushButton_Next.clicked.connect(self.learning_step_4)
        self.label.setPixmap(QPixmap("img/learn/slide3/slide3.png").scaledToWidth(940))
        self.label_2.setPixmap(QPixmap("img/learn/slide3/material_temp.png").scaledToWidth(840))
        #  self.label_2.hide()
        self.label_3.hide()

    def learning_step_4(self):
        self.setWindowTitle(self.tittle + " - шаг 4")
        self.label.clear()
        self.label_2.clear()
        self.label_3.clear()
        self.label.setFixedHeight(680)
        self.label_infoStepCount.setText("Шаг 4")
        self.pushButton_Next.setText("Далее")
        self.label.setPixmap(QPixmap("img/learn/slide4/printer2.png").scaledToWidth(940))
        self.label_2.hide()
        self.label_3.hide()
        self.label_infoStepCount.hide()
        self.pushButton_Back.clicked.connect(self.learning_step_3)
        self.pushButton_Next.clicked.connect(self.learning_step_end)

    def learning_step_end(self):
        self.setWindowTitle(self.tittle + " - конец")
        text_end = "Завершить"
        self.label.clear()
        self.label_2.clear()
        self.label.setPixmap(QPixmap("img/learn/slide4/tech_print2.png").scaledToWidth(940))
        self.label_2.hide()
        self.label_3.hide()
        self.label_infoStepCount.setText("Конец")
        self.label_infoStepCount.hide()
        self.pushButton_Next.setText(text_end)
        self.pushButton_Next.clicked.connect(self.close)


class ExamDialog(QDialog, examDialog.Ui_Dialog):
    def __init__(self, parent=None):
        super(ExamDialog, self).__init__(parent)
        self.setupUi(self)

        if self.radioButtonQuestion1_Answer1.isChecked():
            self.pushButtonExamEnd.setEnabled(True)


        self.radioButtonQuestion1_Answer1.clicked.connect(self.button_active)

        self.pushButtonExamEnd.clicked.connect(self.start_exam)
        # self.pushButtonExamEnd.clicked.connect(self.close)

    def button_active(self):
        self.pushButtonExamEnd.setEnabled(True)

    def start_exam(self):
        color_success = "color:#17883c"
        color_error = "color:#a70f0f"
        total_count = 0

        if self.radioButtonQuestion1_Answer1.isChecked():
            total_count += 1
            self.label_Question1.setStyleSheet(color_success)
        else:
            total_count -= 1
            self.label_Question1.setStyleSheet(color_error)

        if self.radioButtonQuestion2_Answer2.isChecked():
            total_count += 1
            self.label_Question2.setStyleSheet(color_success)
        else:
            total_count -= 1
            self.label_Question2.setStyleSheet(color_error)

        if self.radioButtonQuestion3_Answer2.isChecked():
            total_count += 1
            self.label_Question3.setStyleSheet(color_success)
        else:
            total_count -= 1
            self.label_Question3.setStyleSheet(color_error)

        if self.radioButtonQuestion4_Answer1.isChecked():
            total_count += 1
            self.label_Question4.setStyleSheet(color_success)
        else:
            total_count -= 1
            self.label_Question4.setStyleSheet(color_error)

        if self.radioButtonQuestion5_Answer2.isChecked():
            total_count += 1
            self.label_Question5.setStyleSheet(color_success)
        else:
            total_count -= 1
            self.label_Question5.setStyleSheet(color_error)

        if total_count == 5:
            self.label.setText("На все вопросы дан правильный ответ")
            self.pushButtonExamEnd.setText("Завершить")
            self.pushButtonExamEnd.setStyleSheet("background-color:#17883c; color:#fff;")
            self.pushButtonExamEnd.clicked.connect(self.close)

class AddDialog(QDialog, addDialog.Ui_Dialog):
    def __init__(self, parent=None):
        super(AddDialog, self).__init__(parent)
        self.setupUi(self)


class AboutDialog(QDialog, aboutDialog.Ui_Dialog):
    def __init__(self, parent=None):
        super(AboutDialog, self).__init__(parent)
        self.setupUi(self)


if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)
    login = LoginDialog()
    learn = LearnDialog()

    if login.exec_() == QtWidgets.QDialog.Accepted:
        win = MainApp()
        sys.exit(app.exec_())
