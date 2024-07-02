from datetime import datetime, timedelta
from django.shortcuts import render
from .models import Facerec, Id_persons  # Убедитесь, что это правильный импорт модели
import pytz
import json

def format_timedelta(td):
    # Функция для форматирования timedelta в строку с поддержкой отрицательного времени
    # Сначала получаем общее количество секунд из timedelta
    total_seconds = td.total_seconds()
    # Знак временного интервала
    sign = "-" if total_seconds < 0 else ""
    # Приводим общее количество секунд к абсолютному значению для подсчета
    total_seconds = abs(total_seconds)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{sign}{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

def index(request):
    return render(request, 'report.html')


def get_time_report(request, date):
    start_date = datetime.strptime(date, '%Y-%m-%d')
    normative_work_time = timedelta(hours=8)
    office_arrival_time = datetime.strptime(date + ' 09:00', '%Y-%m-%d %H:%M')
    entries = list(Facerec.objects.filter(time__date=start_date).order_by('id_person', 'time'))
    person_names = {p.id_person: p.person for p in Id_persons.objects.all()}
    timezone = pytz.timezone("Europe/Moscow")
    time_spent_dict = {}
    alarm_count_dict = {}
    office_exit_count_dict = {}
    first_office_entry_dict = {}
    last_event_dict = {}
    late_dict = {}
    late_arrivals = 0  # Для подсчета опозданий, но не выводится в отчет

    for entry in entries:
        person_id = entry.id_person
        if person_id not in time_spent_dict:
            time_spent_dict[person_id] = timedelta()
            alarm_count_dict[person_id] = 0
            office_exit_count_dict[person_id] = 0
            first_office_entry_dict[person_id] = None
            late_dict[person_id] = 0
        if entry.event == 'out':
            office_exit_count_dict[person_id] += 1

        if entry.event == 'in' and (
                first_office_entry_dict[person_id] is None or entry.time.replace(tzinfo=None) < first_office_entry_dict[
            person_id]):
            first_office_entry_dict[person_id] = entry.time.replace(tzinfo=None)
            if entry.time.replace(tzinfo=None) + timedelta(hours=3) > office_arrival_time:
                late_dict[person_id] += 1

        last_event = last_event_dict.get(person_id)
        if last_event:
            if last_event['event'] == 'in' and entry.event == 'out':
                time_spent = entry.time - last_event['time']
                time_spent_dict[person_id] += time_spent
            # Остальная логика обработки событий остается прежней
        last_event_dict[person_id] = {'event': entry.event, 'time': entry.time}

    for person_id, last_event in last_event_dict.items():
        if last_event['event'] == 'in':
            alarm_count_dict[person_id] += 1

    report_data = []
    for id_person in time_spent_dict:
        person_name = person_names.get(id_person, "Unknown")
        deviation = time_spent_dict[id_person] - normative_work_time
        # Преобразуем отклонение в удобный формат строки, если нужно
        deviation_str = format_timedelta(deviation)
        first_entry = first_office_entry_dict[id_person]
        rus_first_entry = first_entry + timedelta(hours=3)
        # if first_entry:
        #     first_entry_local = localtime(first_entry).strftime('%H:%M:%S')
        # else:
        #     first_entry_local = 'Не было входа'

        report_data.append({
            'person': person_name,
            'all_time': str(time_spent_dict[id_person]),
            'deviation': deviation_str,
            'alarm': alarm_count_dict[id_person],
            'office_exits': office_exit_count_dict[id_person],
            'first_entry': rus_first_entry.strftime('%H:%M:%S'),
            'late': late_dict[id_person]
        })

    return render(request, 'table.html', {'report_data': report_data})

def get_time_report_range(request, start_date, end_date):
    with open('/home/user/PycharmProjects/office_rec/officerec/rec/superjob2024.json') as f:
        holidays_data = json.load(f)
    holidays = set(holidays_data['holidays'])
    #timezone = pytz.timezone("Europe/Moscow")
    normative_work_time = timedelta(hours=8)
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')
    # Словари для агрегации данных
    final_time_spent_dict = {}
    final_alarm_count_dict = {}
    final_office_exit_count_dict = {}
    final_late_count_dict = {}
    latest_office_entry_time_dict = {}

    # Перебор дней в выбранном промежутке времени
    current_date = start_date
    working_days = 0

    while current_date <= end_date:
        entries = Facerec.objects.filter(time__date=current_date.date()).order_by('id_person', 'time')
        is_holiday = current_date.strftime('%Y-%m-%d') in holidays
        if not is_holiday:
            working_days += 1
        person_names = {p.id_person: p.person for p in Id_persons.objects.all()}
        office_arrival_time = datetime.combine(current_date.date(), datetime.strptime('09:00', '%H:%M').time())
        time_spent_dict = {}
        alarm_count_dict = {}
        office_exit_count_dict = {}
        first_office_entry_dict = {}
        last_event_dict = {}
        late_dict = {}

        for entry in entries:
            person_id = entry.id_person
            if person_id not in time_spent_dict:
                time_spent_dict[person_id] = timedelta()
                alarm_count_dict[person_id] = 0
                office_exit_count_dict[person_id] = 0
                first_office_entry_dict[person_id] = None
                late_dict[person_id] = 0
            if entry.event == 'out':
                office_exit_count_dict[person_id] += 1
            if entry.event == 'in' and (
                    first_office_entry_dict[person_id] is None or entry.time.replace(tzinfo=None) <
                    first_office_entry_dict[
                        person_id]):
                first_office_entry_dict[person_id] = entry.time.replace(tzinfo=None)
                if entry.time.replace(tzinfo=None) + timedelta(hours=3) > office_arrival_time:
                    late_dict[person_id] += 1

            last_event = last_event_dict.get(person_id)
            if last_event:
                if last_event['event'] == 'in' and entry.event == 'out':
                    time_spent = entry.time - last_event['time']
                    time_spent_dict[person_id] += time_spent
                # Остальная логика обработки событий остается прежней
            last_event_dict[person_id] = {'event': entry.event, 'time': entry.time}

        for person_id, last_event in last_event_dict.items():
            if last_event['event'] == 'in':
                alarm_count_dict[person_id] += 1
            # Обработка событий входа/выхода, аналогично вашей логике в get_time_report

        # Агрегация данных
        for person_id in time_spent_dict:
            final_time_spent_dict[person_id] = final_time_spent_dict.get(person_id, timedelta()) + time_spent_dict[
                person_id]
            final_alarm_count_dict[person_id] = final_alarm_count_dict.get(person_id, 0) + alarm_count_dict.get(
                person_id, 0)
            final_office_exit_count_dict[person_id] = final_office_exit_count_dict.get(person_id,
                                                                                       0) + office_exit_count_dict.get(
                person_id, 0)
            final_late_count_dict[person_id] = final_late_count_dict.get(person_id, 0) + late_dict.get(person_id, 0)
            if first_office_entry_dict[person_id] is not None:
                if person_id not in latest_office_entry_time_dict or first_office_entry_dict[person_id] > \
                        latest_office_entry_time_dict[person_id]:
                    latest_office_entry_time_dict[person_id] = first_office_entry_dict[person_id]

        current_date += timedelta(days=1)




    # Формирование итогового отчета
    report_data = []
    #total_days = (end_date - start_date).days + 1
    for person_id, time_spent in final_time_spent_dict.items():
        person_name = person_names.get(person_id, "Unknown")
        total_normative_work_time = normative_work_time * working_days
        deviation = time_spent - total_normative_work_time
        deviation_str = format_timedelta(deviation)
        latest_entry = latest_office_entry_time_dict.get(person_id)
        latest_entry_va = (latest_entry + timedelta(hours=3)) if latest_entry is not None else 'Нет данных'

        report_data.append({
            'person': person_name,
            'all_time': format_timedelta(time_spent),
            'deviation': deviation_str,
            'alarm': final_alarm_count_dict[person_id],
            'office_exits_average': round(final_office_exit_count_dict[person_id] / working_days),
            'late': final_late_count_dict[person_id],
            'latest_entry': latest_entry_va.strftime('%H:%M:%S')
        })

    return render(request, 'weekly.html', {'report_data': report_data})























# def get_time_report_range(request, start_date, end_date):
#     start_date = datetime.strptime(start_date, '%Y-%m-%d')
#     end_date = datetime.strptime(end_date, '%Y-%m-%d')
#
#     final_time_spent_dict = {}
#     final_alarm_count_dict = {}
#
#     current_date = start_date
#     while current_date <= end_date:
#         entries = Facerec.objects.filter(time__date=current_date).order_by('id_person', 'time')
#         time_spent_dict = {}
#         alarm_count_dict = {}
#         last_event_dict = {}
#
#         for entry in entries:
#             person_id = entry.id_person
#             if person_id not in time_spent_dict:
#                 time_spent_dict[person_id] = timedelta()
#                 alarm_count_dict[person_id] = 0
#
#             last_event = last_event_dict.get(person_id)
#
#             if last_event:
#                 if last_event['event'] == 'in' and entry.event == 'out':
#                     time_spent = entry.time - last_event['time']
#                     time_spent_dict[person_id] += time_spent
#                 elif last_event['event'] == 'out' and entry.event == 'out':
#                     alarm_count_dict[person_id] += 1
#                 elif last_event['event'] == 'in' and entry.event == 'in':
#                     pass  # Повторное 'in' не увеличивает аларм
#             else:
#                 if entry.event == 'out':
#                     alarm_count_dict[person_id] += 1  # Первый 'out' без 'in'
#
#             last_event_dict[person_id] = {'event': entry.event, 'time': entry.time}
#
#         for person_id, last_event in last_event_dict.items():
#             if last_event['event'] == 'in':
#                 alarm_count_dict[person_id] += 1  # Незакрытый интервал в конце дня
#
#         # Агрегация результатов за день в итоговые словари
#         for person_id, time_spent in time_spent_dict.items():
#             final_time_spent_dict[person_id] = final_time_spent_dict.get(person_id, timedelta()) + time_spent
#
#         for person_id, alarm_count in alarm_count_dict.items():
#             final_alarm_count_dict[person_id] = final_alarm_count_dict.get(person_id, 0) + alarm_count
#
#         current_date += timedelta(days=1)
#
#     # Подготовка итоговых данных для отображения в шаблоне
#     report_data = [
#         {
#             'person': person_id,
#             'all_time': str(final_time_spent_dict[person_id]),
#             'alarm': final_alarm_count_dict[person_id]
#         } for person_id in final_time_spent_dict
#     ]
#
#     return render(request, 'weekly.html', {'report_data': report_data})
