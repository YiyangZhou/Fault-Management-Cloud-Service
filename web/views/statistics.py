import collections
import pandas
import numpy
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Count
from web import models
import jieba.analyse
from string import digits
from utils.cut import rep_invalid_char, cut_word


def statistics(request, project_id):
    """ 统计页面 """
    #########################
    # 1.从数据库导入待预测数据
    title = []
    content = []
    for i in range(len(models.Issues.objects.filter(project=project_id))):
        title.append(models.Issues.objects.filter(project=project_id)[i].subject)
        content.append(models.Issues.objects.filter(project=project_id)[i].desc)

    # 2.把待处理数据连接起来放到一个列表中
    content_list = []
    for i in range(len(title)):
        content_list.append(
            [rep_invalid_char(str(title[i]) + str(content[i])).translate(str.maketrans('', '', digits))])
    # 3.分词操作
    Jie_content = []
    for item in content_list:
        split_content = cut_word(item)

        for i in split_content:
            res = i.split()  # 不加任何参数
            for n in res:
                Jie_content.append(n)

    # 4.去除停用词
    stopwords = pandas.read_csv('utils//stop_words.txt', sep='\t', quoting=3,
                                names=['stopwords'], index_col=False,
                                encoding='utf-8')

    array_data = numpy.array(stopwords)  # df数据转为np.ndarray()
    list_data = array_data.tolist()  # 将np.ndarray()转为列表
    stop_list = []
    for item in list_data:
        for i in item:
            stop_list.append(i)
    clean_content = []
    all_words = []
    for j_content in Jie_content:

        if j_content in stop_list:
            continue

        clean_content.append(j_content)
    # 5.使用jieba分词器提取关键字
    content_word = ''
    content_word = ''.join(clean_content)
    content_text = ' '.join(jieba.analyse.extract_tags(content_word, topK=10, withWeight=False))
    data_result_dict = {}
    i = 0
    for keyword, weight in jieba.analyse.extract_tags(content_word, withWeight=True, topK=10):
        data_result_dict[i] = {'name': keyword, "value": weight}
        i += 1
    # context = {
    #     'data': {
    #         'data': list(data_result_dict.values())
    #     }
    # }

    return render(request, 'statistics.html', {"data": list(data_result_dict.values())})


def statistics_priority(request, project_id):
    """ 按照优先级生成饼图 """

    # 找到所有的问题，根据优先级分组，每个优先级的问题数量
    start = request.GET.get('start')
    end = request.GET.get('end')

    # 1.构造字典
    data_dict = collections.OrderedDict()
    for key, text in models.Issues.priority_choices:
        data_dict[key] = {'name': text, 'y': 0}

    # 2.去数据查询所有分组得到的数据量
    result = models.Issues.objects.filter(project_id=project_id, create_datetime__gte=start,
                                          create_datetime__lt=end).values('priority').annotate(ct=Count('id'))

    # 3.把分组得到的数据更新到data_dict中
    for item in result:
        data_dict[item['priority']]['y'] = item['ct']

    return JsonResponse({'status': True, 'data': list(data_dict.values())})


def statistics_project_user(request, project_id):
    """ 项目成员每个人被分配的任务数量（问题类型的配比）"""
    start = request.GET.get('start')
    end = request.GET.get('end')

    # 1. 所有项目成员 及 未指派
    all_user_dict = collections.OrderedDict()
    all_user_dict[request.tracer.project.creator.id] = {
        'name': request.tracer.project.creator.username,
        'status': {item[0]: 0 for item in models.Issues.status_choices}
    }
    all_user_dict[None] = {
        'name': '未指派',
        'status': {item[0]: 0 for item in models.Issues.status_choices}
    }
    user_list = models.ProjectUser.objects.filter(project_id=project_id)
    for item in user_list:
        all_user_dict[item.user_id] = {
            'name': item.user.username,
            'status': {item[0]: 0 for item in models.Issues.status_choices}
        }

    # 2. 去数据库获取相关的所有问题
    issues = models.Issues.objects.filter(project_id=project_id, create_datetime__gte=start, create_datetime__lt=end)
    for item in issues:
        if not item.assign:
            all_user_dict[None]['status'][item.status] += 1
        else:
            all_user_dict[item.assign_id]['status'][item.status] += 1

    # 3.获取所有的成员
    categories = [data['name'] for data in all_user_dict.values()]

    # 4.构造字典
    """
    data_result_dict = {
        1:{name:新建,data:[1，2，3，4]},
        2:{name:处理中,data:[3，4，5]},
        3:{name:已解决,data:[]},
        4:{name:已忽略,data:[]},
        5:{name:待反馈,data:[]},
        6:{name:已关闭,data:[]},
        7:{name:重新打开,data:[]},
    }
    """
    data_result_dict = collections.OrderedDict()
    for item in models.Issues.status_choices:
        data_result_dict[item[0]] = {'name': item[1], "data": []}

    for key, text in models.Issues.status_choices:
        # key=1,text='新建'
        for row in all_user_dict.values():
            count = row['status'][key]
            data_result_dict[key]['data'].append(count)

    context = {
        'status': True,
        'data': {
            'categories': categories,
            'series': list(data_result_dict.values())
        }
    }

    return JsonResponse(context)


def statistics_problem(request, project_id):
    id = models.Issues.objects.filter(project_id=project_id).all()

    py_count = 0
    c_count = 0
    java_count = 0
    git_count = 0
    other_count = 0
    data_count = 0
    front_count = 0
    back_count = 0
    name_list = ['python', 'C语言', 'java', 'git', '其他', '数据库', '前端', '功能']
    data_result_dict = {}
    for i in range(1, 9):
        data_result_dict[i] = {'name': name_list[i-1], "data": None}
    for item in id:

        if item.issues_type.title == 'python':
            py_count += 1
        if item.issues_type.title == 'C语言':
            c_count += 1
        if item.issues_type.title == 'java':
            java_count += 1
        if item.issues_type.title == 'git':
            git_count += 1
        if item.issues_type.title == '其他':
            other_count += 1
        if item.issues_type.title == '数据库':
            data_count += 1
        if item.issues_type.title == '前端':
            front_count += 1
        if item.issues_type.title == '功能':
            back_count += 1

    py_list = [py_count]
    c_list = [0, c_count]
    java_list = [0, 0, java_count]
    git_list = [0, 0, 0, git_count]
    other_list = [0, 0, 0, 0, other_count]
    data_list = [0, 0, 0, 0, 0, data_count]
    front_list = [0, 0, 0, 0, 0, 0, front_count]
    back_list = [0, 0, 0, 0, 0, 0, 0, back_count]
    data_result_dict[1]['data'] = py_list
    data_result_dict[2]['data'] = c_list
    data_result_dict[3]['data'] = java_list
    data_result_dict[4]['data'] = git_list
    data_result_dict[5]['data'] = other_list
    data_result_dict[6]['data'] = data_list
    data_result_dict[7]['data'] = front_list
    data_result_dict[8]['data'] = back_list

    context = {
        'data': {
            'series': list(data_result_dict.values())
        }
    }

    return JsonResponse(context)



