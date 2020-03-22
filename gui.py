#!usr/bin/python3
"""
@author:    Jokin
@link:      https://github.com/jokin1999/SMMS_Uploader
"""
# -*- coding: utf-8 -*-

import os
import re
import time
import base64
import tempfile
import threading
import tkinter as tk
import tkinter.ttk
import tkinter.messagebox
import tkinter.filedialog
import win32clipboard as wcb
import ico
from scanner import scanner
from smms import smms
from cloud import smcloud


# 消息盒子定义
def msgbox(message, title='提示', type='info'):
    if (type == 'info'):
        tk.messagebox.showinfo(title=title, message=message)
    elif (type == 'warning'):
        tk.messagebox.showwarning(title=title, message=message)
    elif (type == 'error'):
        tk.messagebox.showerror(title=title, message=message)


# 文件选择器
def selector(mode=0):
    global _files
    filetypes = ['.png', '.jpg', 'gif']
    filetypes_2 = [('Image files', '*.png;*.jpg;*.gif')]
    if (mode == 0):
        print('单文件选择')
        files = tk.filedialog.askopenfilename(filetypes=filetypes_2)
        _files.append(files)
    elif (mode == 1):
        print('多文件选择')
        files = tk.filedialog.askopenfilenames(filetypes=filetypes_2)
        _files.extend(list(files))
    elif (mode == 2):
        print('文件夹遍历')
        directory = tk.filedialog.askdirectory()
        if not directory == '':
            scan = scanner()
            _files.extend(scan.scan(directory, filetypes))
    elif (mode == 3):
        # 单层文件夹
        # _files = tk.filedialog.askopenfilenames()
        pass
    # 去重
    _files = list(set(_files))
    # 美化
    for filename in _files:
        _files[_files.index(filename)] = filename.replace('\\', '/')
    # 显示于列表
    _files.sort()
    lsbox_files.set(_files)


def listboxRenew(Listbox_var, list):
    Listbox_var.set(list)


def listRemove(list, removalList):
    for li in removalList:
        list.remove(li)
    return list


def getListboxValueByList(listbox, list):
    values = []
    for li in list:
        values.append(listbox.get(li))
    return values


def _lsbox_remove():
    global _files
    listboxRenew(lsbox_files, listRemove(_files, getListboxValueByList(lsbox, list(lsbox.curselection()))))
    lsbox.select_clear(0, len(_files)-1)


def _treeview_copy(type):
    list = []
    for item in treeview.selection():
        item_text = treeview.item(item, 'values')
        list.append(item_text[type])
    list = '\r\n'.join(list)
    # 复制到剪贴板
    wcb.OpenClipboard()
    wcb.EmptyClipboard()
    wcb.SetClipboardText(list)
    wcb.CloseClipboard()


def _treeview_delete():
    global TVFILE
    for item in treeview.selection():
        item_value = ','.join(treeview.item(item, 'values'))
        treeview.delete(item)
        try:
            with open(TVFILE, 'r+', encoding='utf-8') as f:
                data = f.read()
        except Exception:
            show_status('读取记录时出错，删除失败')
        else:
            data = data.split('\n')
            data.remove(item_value)
            try:
                with open(TVFILE, 'w+', encoding='utf-8') as f:
                    f.write('\n'.join(data))
            except Exception:
                show_status('删除时出错，删除失败')


def _lsbx_rb(event):
    if not (len(lsbox.curselection()) == 0):
        lsbx_rbmenu.post(event.x_root, event.y_root)


def _treeview_rb(event):
    if not (len(treeview.selection()) == 0):
        treeview_rbmenu.post(event.x_root, event.y_root)


# 读取上传列表
def readSuccessList(filename='./save.txt'):
    if not (os.path.exists(filename)):
        return []
    list = []
    file = open(filename, 'r+', encoding='utf-8')
    filelists = file.readlines()
    for filelist in filelists:
        info = filelist.strip().split(sep=',', maxsplit=2)
        info[0] = info[0].replace('\\', '/')
        list.append(tuple(info))
    return list


def switch_list(filename='./save.txt'):
    global TVFILE
    TVFILE = filename
    list_data = readSuccessList(filename)
    for item in treeview.get_children():
        treeview.delete(item)
    for sup in list_data:
        treeview.insert('', list_data.index(sup), value=sup)


def operating_area(state=0):
    if (state == 0):
        # 闲置模式
        btn_selector['state'] = tk.NORMAL
        btn_upload['state'] = tk.NORMAL
        btn_pause['state'] = tk.DISABLED
    elif (state == 1):
        # 上传模式
        btn_selector['state'] = tk.DISABLED
        btn_upload['state'] = tk.DISABLED
        btn_pause['state'] = tk.NORMAL


# 开始上传
def _start_upload():
    global t_upload
    operating_area(1)
    t_upload['status'] = True
    t_upload['thread'] = threading.Thread(target=upload, args=[lsbox_files], daemon=True)
    t_upload['thread'].start()


def show_status(text):
    label3_bottom['text'] = text


# 停止上传
def _stop_upload():
    global t_upload
    try:
        t_upload['status'] = False
    finally:
        print('停止上传')
    operating_area(0)
    show_status('就绪')


# 变量调整器
def _t_upload(var, value):
    global t_upload
    t_upload[var] = value


# 上传队列中的文件
def upload(Listbox_var):
    global _files
    global t_upload
    uploader = smms()
    while len(_files) != 0:
        is_upload = True
        is_insert = False
        show_status('上传准备中')
        # 判断是否要求结束或暂停
        if (t_upload['status'] is False):
            show_status('上传已终止')
            break
        elif (t_upload['status'] == 'pause'):
            print('upload paused')
            while(t_upload['status'] == 'pause'):
                pass
        show_status('准备文件中')
        file = _files[0]
        # 检查文件大小
        if (vSL.get() == 1):
            show_status('检查文件大小中')
            try:
                fsize = os.path.getsize(file)
            except Exception:
                fsize = False
            if (fsize is False):
                is_upload = True
                print('获取文件大小失败，尝试上传')
            else:
                if (fsize > (5 * 1024 * 1024)):
                    is_upload = False
                    err_msg = 'File is too large.'
                    show_status('文件过大')
            show_status('读取文件：' + os.path.basename(file))
            try:
                with open(file, 'rb') as file_open:
                    file_data = file_open.read()
            except Exception:
                is_upload = False
                err_msg = 'Failed to open file.'
                show_status('读取文件失败')
        if (is_upload is True):
            show_status('上传文件：' + os.path.basename(file))
            res = uploader.post(file, file_data)
            res = uploader.parse_json(res)
            show_status('解析结果中')
        else:
            res = {'code': 'error', 'message': err_msg}

        # 解析结果
        if (res['code'] == 'success' and 'message' not in res):
            # 成功删除此项任务
            is_insert = True
            _files.remove(file)
            cdn = res['data']['url']
            delete = res['data']['delete']
            # 本地路径-在线地址-删除地址
            file_open = open('save.txt', 'a+', newline='\n', encoding='utf-8')
            file_open.write(str(file.encode('utf-8'), 'utf-8') + ',' + cdn + ',' + delete + '\n')
            file_open.close()
        else:
            cdn = 'error'
            delete = res['message']
            # 文件过大或不支持的后缀名或无法存储或空文档
            exception = [
                'File is empty.',
                'File is too large.',
                'File has an invalid extension.',
                'Could not save uploaded file.',
                'Request Entity Too Large.',
                'No files were uploaded.',
                'Failed to open file.'
            ]
            search = re.search(r'left\s(\d{1,})\ssecond', delete)
            if (delete in exception):
                _files.remove(file)
                is_insert = True
            else:
                is_insert = False
                if (search is not None):
                    restTime = int(search.group(1))
                    interval = 1
                    print('上传频率限制，' + str(restTime) + '秒后继续上传')
                    while restTime > 0:
                        # 检测状态
                        if (t_upload['status'] is False):
                            show_status('上传已终止')
                            break
                        restTime -= interval
                        show_status('上传频率限制，' + str(restTime) + '秒后继续上传')
                        time.sleep(interval)
                # urllib3报错
                if (delete == 'Connection failed.'):
                    show_status('连接服务器失败，3秒后重试')
                    time.sleep(3)
                # 上传频率过快
                if (delete == 'Upload file frequency limit.'):
                    show_status('上传频率过快，3秒后继续上传')
                    time.sleep(3)
                # 返回值不匹配
                if (delete == 'Bad Json Data.'):
                    show_status('无法解析服务器响应')
                    break

            # 失败文件- 失败原因
            file_open = open('fail.txt', 'a', newline='\n', encoding='utf-8')
            file_open.write(file + ',' + res['message'] + '\n')
            file_open.close()

            # 上传失败处理
            if (res['code'] == 'image_repeated'):
                #重复文件处理
                show_status('文件已经存在于服务器')
                is_insert = True
                _files.remove(file)
                cdn = res['images']
                delete = '[repeated] no delete url'
                # 本地路径-在线地址-删除地址
                file_open = open('save.txt', 'a+', newline='\n', encoding='utf-8')
                file_open.write(str(file.encode('utf-8'), 'utf-8') + ',' + cdn + ',' + delete + '\n')
                file_open.close()

        data = (file, cdn, delete)
        if (is_insert is True):
            treeview.insert('', 'end', value=data)
        listboxRenew(Listbox_var, _files)
        # 暂停1秒以避免错误
        time.sleep(upload_delay)
    t_upload['status'] = False
    time.sleep(3)
    show_status('就绪')
    operating_area(0)


if __name__ == '__main__':
    # 版本定义
    VERSION = '1.0.7'
    # 上传延迟
    upload_delay = 0
    # 多线程定义
    t_upload = {}
    # 文件选择器返回值
    _files = []
    # 当前Treeview listfile
    TVFILE = './save.txt'
    # 上传模式定义
    upload_modes = [('单个上传', 0, 'normal'), ('群组上传', 1, 'disable')]
    # 选择模式定义
    selector_modes = [('单文件选择', 0, 'normal'), ('多文件选择', 1, 'normal'), ('文件夹遍历', 2, 'normal'), ('单层文件夹', 3, 'disable')]
    # 创建窗口
    win = tk.Tk()
    win.resizable(width=False, height=False)
    tempfile = tempfile.mktemp()
    icon = open(tempfile, 'wb')
    icon.write(base64.b64decode(ico.ico))
    icon.close()
    win.iconbitmap(tempfile)
    os.remove(tempfile)

    win.title('SMMS图床上传工具 ' + VERSION)

    # 读取已上传列表
    sUpload = readSuccessList()

    mainFrame = tk.Frame(win)
    mainFrame.grid()

    # 模式标签框架
    lf_mode = tk.LabelFrame(mainFrame, text='上传模式', fg='blue')
    lf_mode.grid(row=1, column=0, padx=10, pady=10, sticky=tk.N+tk.S+tk.E+tk.W)
    # 创建RadioButton
    vUpload = tk.IntVar()
    for mode, num, state in upload_modes:
        rb = tk.Radiobutton(lf_mode, text=mode, variable=vUpload, value=num, state=state)
        rb.pack()
        vUpload.set(0)

    # 其他选项框架
    lf_others = tk.LabelFrame(mainFrame, text='其他', fg='blue')
    lf_others.grid(row=0, column=3, rowspan=2, padx=10, pady=10, sticky=tk.N+tk.S+tk.E+tk.W)
    vDR = tk.IntVar()
    vSL = tk.IntVar()
    vSL.set(1)
    cb_duplicateRemoval = tk.Checkbutton(lf_others, text='检查上传重复（本地）', variable=vDR, state=tk.DISABLED)
    cb_duplicateRemoval.grid(row=0, column=0, sticky=tk.W)
    cb_sizeLimitation = tk.Checkbutton(lf_others, text='过滤大于5M的文件', variable=vSL, state=tk.NORMAL)
    cb_sizeLimitation.grid(row=1, column=0, sticky=tk.W)
    btn_cloud = tk.Button(lf_others, text='切换中继', command=smcloud)
    btn_cloud.grid(row=2, column=0, sticky=tk.W+tk.E, padx=5)
    btn_relay_list = tk.Button(lf_others, text='切换已转换列表', command=lambda: switch_list('./save2.txt'))
    btn_relay_list.grid(row=3, column=0, sticky=tk.W+tk.E, padx=5)
    btn_origin_list = tk.Button(lf_others, text='切换已上传列表', command=lambda: switch_list('./save.txt'))
    btn_origin_list.grid(row=4, column=0, sticky=tk.W+tk.E, padx=5)

    # 选择器模式标签框架
    lf_selector_mode = tk.LabelFrame(mainFrame, text='选择器模式', fg='blue')
    lf_selector_mode.grid(row=0, column=0, padx=10, pady=10, sticky=tk.N+tk.S+tk.E+tk.W)
    # RadioButton
    vSelector = tk.IntVar()
    for mode, num, state in selector_modes:
        rb = tk.Radiobutton(lf_selector_mode, text=mode, variable=vSelector, value=num, state=state)
        rb.pack()
        # 默认多文件选择
        vSelector.set(1)

    # 操作区
    lf_operator = tk.LabelFrame(mainFrame, text='操作区', fg='blue')
    lf_operator.grid(row=0, rowspan=2, column=1, padx=10, pady=10, sticky=tk.N+tk.S+tk.E+tk.W)
    # RadioButton
    btn_selector = tk.Button(lf_operator, text='选择', width=10, command=lambda: selector(vSelector.get()))
    btn_selector.grid(padx=10, pady=10, sticky=tk.N+tk.S+tk.E+tk.W)
    btn_upload = tk.Button(lf_operator, text='上传', width=10, command=lambda: _start_upload())
    btn_upload.grid(padx=10, pady=10, sticky=tk.N+tk.S+tk.E+tk.W)
    btn_pause = tk.Button(lf_operator, text='暂停', width=10, command=lambda: _stop_upload())
    btn_pause['state'] = tk.DISABLED
    btn_pause.grid(padx=10, pady=10, sticky=tk.N+tk.S+tk.E+tk.W)

    # 已选文件列表
    lf_lsbox = tk.LabelFrame(mainFrame, text='等待上传文件列表', fg='red')
    lf_lsbox.grid(row=0, rowspan=2, column=2, padx=10, pady=10, sticky=tk.N+tk.S+tk.E+tk.W)
    lsbox_files = tk.StringVar()
    lsbox = tk.Listbox(lf_lsbox, selectmode=tk.EXTENDED, listvariable=lsbox_files, width=75, relief=tk.FLAT)
    lsbox.grid(row=0, column=0)
    # 右键菜单
    lsbx_rbmenu = tk.Menu(lsbox, tearoff=False)
    lsbx_rbmenu.add_command(label='删除', command=_lsbox_remove)
    # lsbox.bind('<Button-3>', func=lambda event: lsbx_rbmenu.post(event.x_root, event.y_root))
    lsbox.bind('<ButtonRelease-3>', func=lambda event: _lsbx_rb(event))
    # 滚动条
    lsbox_yscrollbar = tk.Scrollbar(lf_lsbox, command=lsbox.yview)
    lsbox_yscrollbar.grid(row=0, column=1, sticky=tk.N+tk.S+tk.E+tk.W)
    lsbox.config(yscrollcommand=lsbox_yscrollbar.set)
    lsbox_xscrollbar = tk.Scrollbar(lf_lsbox, command=lsbox.xview, orient='horizontal')
    lsbox_xscrollbar.grid(row=1, column=0, sticky=tk.N+tk.S+tk.E+tk.W)
    lsbox.config(xscrollcommand=lsbox_xscrollbar.set)

    # 已上传文件列表
    lf_treeview = tk.LabelFrame(mainFrame, text='已上传文件列表（右键复制 | CTRL多选）', fg='green')
    lf_treeview.grid(row=2, column=0, columnspan=4, padx=10, pady=5, sticky=tk.N+tk.S+tk.E+tk.W)
    treeview = tk.ttk.Treeview(lf_treeview, columns=['path', 'cdn', 'delete'], show='headings', height=10)
    treeview.grid(sticky=tk.N+tk.S+tk.E+tk.W)
    treeview.column('path', width=550, anchor='w')
    treeview.column('cdn', width=200, anchor='w')
    treeview.column('delete', width=200, anchor='w')
    treeview.heading('path', text='本地路径')
    treeview.heading('cdn', text='CDN链接')
    treeview.heading('delete', text='删除链接')
    for sup in sUpload:
        treeview.insert('', sUpload.index(sup), value=sup)
        # id = treeview.insert('', sUpload.index(sup), value=sup)
    # 滚动条
    treeview_sby = tk.Scrollbar(lf_treeview, orient=tk.VERTICAL, command=treeview.yview)
    treeview.configure(yscrollcommand=treeview_sby.set)
    treeview_sby.grid(row=0, column=1, sticky=tk.N+tk.S)
    # 右键菜单
    treeview_rbmenu = tk.Menu(treeview, tearoff=False)
    treeview_rbmenu.add_command(label='复制CDN地址', command=lambda: _treeview_copy(1))
    treeview_rbmenu.add_command(label='复制删除地址', command=lambda: _treeview_copy(2))
    treeview_rbmenu.add_command(label='复制本地路径', command=lambda: _treeview_copy(0))
    treeview_rbmenu.add_separator()
    treeview_rbmenu.add_command(label='删除记录', command=lambda: _treeview_delete())
    treeview.bind('<ButtonRelease-3>', func=lambda event: _treeview_rb(event))

    # Footer
    label_bottom = tk.Label(mainFrame, text='使用须知', fg='#878787')
    label_bottom_info = '1、不得将本工具用作任何商业用途\n2、请严格遵守SM.MS图床的相关使用规定\n3、上传的内容与本工具及本工具作者无关'
    label_bottom.bind('<Button-1>', lambda t: msgbox(label_bottom_info, title='使用须知'))
    label_bottom.grid(row=3, column=0, padx=10, sticky=tk.W)
    label2_bottom = tk.Label(mainFrame, text='Made by Joe', fg='#878787')
    label2_bottom_info = '作者：Joe\n鸣谢：SM.MS图床\n本程序开源免费，若有不良商家售卖，给差评！'
    label2_bottom.bind('<Double-Button-1>', lambda t: msgbox(label2_bottom_info, title='关于作者'))
    label2_bottom.grid(row=3, column=3, padx=5, sticky=tk.E)
    label3_bottom = tk.Label(mainFrame, text='就绪', fg='#fa6333')
    label3_bottom.grid(row=3, column=1, columnspan=2, padx=10, sticky=tk.W+tk.S)

    # 循环
    tk.mainloop()
