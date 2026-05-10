import json
import os
from datetime import datetime, timedelta
from typing import List, Optional


# ======================== Класс Goal ========================
class Goal:
    """Класс, представляющий одну цель накопления."""

    def __init__(self, name: str, target_amount: float, category: str,
                 current_balance: float = 0.0, status: str = "активна",
                 deadline: Optional[str] = None, reminder_threshold: float = 100.0):
        self.name = name
        self.target_amount = target_amount
        self.category = category
        self.current_balance = current_balance
        self.status = status
        self.deadline = deadline  # строка в формате "YYYY-MM-DD"
        self.reminder_threshold = reminder_threshold  # процент для уведомления
        self.history: List[dict] = []  # история изменений баланса

        # Если цель создается с нуля, добавляем начальную запись в историю
        if not self.history and current_balance > 0:
            self._add_history_record(f"Начальный баланс: {current_balance}")

    def _add_history_record(self, description: str):
        """Добавить запись в историю изменений."""
        self.history.append({
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "description": description
        })

    def add_money(self, amount: float) -> bool:
        """Увеличить баланс. Возвращает True, если сумма была добавлена."""
        if amount <= 0:
            print("Сумма должна быть положительной.")
            return False

        new_balance = self.current_balance + amount
        if new_balance > self.target_amount:
            print(f"Превышение итоговой суммы! Максимум: {self.target_amount - self.current_balance:.2f}")
            return False

        self.current_balance = new_balance
        self._add_history_record(f"Пополнение на {amount:.2f}. Баланс: {self.current_balance:.2f}")

        # Проверка на достижение цели
        if self.current_balance >= self.target_amount and self.status != "выполнена":
            self.status = "выполнена"
            self._add_history_record("Цель достигнута!")
            print(f"🎉 Поздравляем! Цель '{self.name}' выполнена!")
        else:
            # Проверка на достижение порога уведомления
            progress = self.get_progress_percent()
            if progress >= self.reminder_threshold and not hasattr(self, '_reminded_for_' + str(
                    int(self.reminder_threshold))):
                print(f"🔔 Уведомление: цель '{self.name}' достигла {progress:.1f}% выполнения!")
                setattr(self, '_reminded_for_' + str(int(self.reminder_threshold)), True)

        return True

    def withdraw_money(self, amount: float) -> bool:
        """Уменьшить баланс (снятие). Возвращает True, если операция выполнена."""
        if amount <= 0:
            print("Сумма должна быть положительной.")
            return False

        if amount > self.current_balance:
            print(f"Недостаточно средств. Доступно: {self.current_balance:.2f}")
            return False

        self.current_balance -= amount
        self._add_history_record(f"Снятие {amount:.2f}. Баланс: {self.current_balance:.2f}")

        # Если цель была выполнена, а потом сняли деньги — статус меняется обратно
        if self.current_balance < self.target_amount and self.status == "выполнена":
            self.status = "активна"
            self._add_history_record("Статус изменён на 'активна' после снятия средств.")

        return True

    def get_progress_percent(self) -> float:
        """Возвращает процент выполнения цели."""
        if self.target_amount == 0:
            return 100.0
        return (self.current_balance / self.target_amount) * 100.0

    def to_dict(self) -> dict:
        """Сериализация объекта в словарь для JSON."""
        return {
            "name": self.name,
            "target_amount": self.target_amount,
            "category": self.category,
            "current_balance": self.current_balance,
            "status": self.status,
            "deadline": self.deadline,
            "reminder_threshold": self.reminder_threshold,
            "history": self.history
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Goal':
        """Восстановление объекта из словаря."""
        goal = cls(
            name=data["name"],
            target_amount=data["target_amount"],
            category=data["category"],
            current_balance=data["current_balance"],
            status=data["status"],
            deadline=data.get("deadline"),
            reminder_threshold=data.get("reminder_threshold", 100.0)
        )
        goal.history = data.get("history", [])
        return goal

    def __str__(self) -> str:
        progress = self.get_progress_percent()
        deadline_str = f", Дедлайн: {self.deadline}" if self.deadline else ""
        return (f"📌 {self.name} | {self.category} | {self.status} | "
                f"{self.current_balance:.2f} / {self.target_amount:.2f} ({progress:.1f}%){deadline_str}")


# ======================== Класс PiggyBank ========================
class PiggyBank:
    """Основной класс приложения Копилка."""

    def __init__(self, data_file: str = "piggybank_data.json"):
        self.data_file = data_file
        self.goals: List[Goal] = []
        self.categories = ["Работа", "Здоровье", "Образование", "Путешествия", "Покупки", "Другое"]
        self.load_data()

    def save_data(self):
        """Сохранить все данные в JSON-файл."""
        data = {
            "goals": [goal.to_dict() for goal in self.goals],
            "categories": self.categories
        }
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def load_data(self):
        """Загрузить данные из JSON-файла."""
        if not os.path.exists(self.data_file):
            return

        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.goals = [Goal.from_dict(g) for g in data.get("goals", [])]
            if "categories" in data:
                self.categories = data["categories"]
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Ошибка загрузки данных: {e}. Будет создан новый файл.")

    def add_goal(self):
        """Добавить новую цель."""
        print("\n--- Добавление новой цели ---")
        name = input("Название цели: ").strip()
        if not name:
            print("Название не может быть пустым.")
            return

        try:
            target_amount = float(input("Итоговая сумма: "))
            if target_amount <= 0:
                print("Сумма должна быть положительной.")
                return
        except ValueError:
            print("Ошибка: введите число.")
            return

        print("Доступные категории:", ", ".join(self.categories))
        category = input("Категория (можно ввести новую): ").strip()
        if not category:
            category = "Другое"
        if category not in self.categories:
            self.categories.append(category)

        # Дополнительно: можно сразу задать дату дедлайна
        set_deadline = input("Установить дедлайн? (д/н): ").strip().lower()
        deadline = None
        if set_deadline == "д":
            deadline_str = input("Дата завершения (ГГГГ-ММ-ДД): ")
            try:
                datetime.strptime(deadline_str, "%Y-%m-%d")
                deadline = deadline_str
            except ValueError:
                print("Неверный формат. Дедлайн не установлен.")

        goal = Goal(name, target_amount, category, deadline=deadline)
        self.goals.append(goal)
        self.save_data()
        print(f"✅ Цель '{name}' добавлена!")

    def edit_balance(self):
        """Изменить баланс цели (пополнить или снять)."""
        if not self.goals:
            print("Нет целей для редактирования.")
            return

        self.list_goals()
        try:
            idx = int(input("Выберите номер цели: ")) - 1
            if idx < 0 or idx >= len(self.goals):
                print("Неверный номер.")
                return
            goal = self.goals[idx]
        except ValueError:
            print("Ошибка ввода.")
            return

        print(f"Выбрана цель: {goal.name}")
        print(f"Текущий баланс: {goal.current_balance:.2f} / {goal.target_amount:.2f}")
        action = input("Что сделать? (+ пополнить, - снять): ").strip()

        try:
            amount = float(input("Сумма: "))
        except ValueError:
            print("Ошибка: введите число.")
            return

        if action == "+":
            goal.add_money(amount)
        elif action == "-":
            goal.withdraw_money(amount)
        else:
            print("Неверное действие.")
            return

        self.save_data()
        print("Баланс обновлён.")

    def list_goals(self):
        """Вывести список всех целей с нумерацией."""
        if not self.goals:
            print("Нет сохранённых целей.")
            return
        print("\n--- Список целей ---")
        for i, goal in enumerate(self.goals, start=1):
            print(f"{i}. {goal}")

    def view_progress(self):
        """Просмотреть прогресс по конкретной цели или всем."""
        if not self.goals:
            print("Нет целей.")
            return

        self.list_goals()
        choice = input("Введите номер цели для детального просмотра (0 - для всех): ").strip()

        if choice == "0":
            self.show_overall_progress()
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(self.goals):
                    goal = self.goals[idx]
                    print(f"\n📊 Прогресс по цели '{goal.name}':")
                    print(f"   Баланс: {goal.current_balance:.2f} / {goal.target_amount:.2f}")
                    print(f"   Процент: {goal.get_progress_percent():.1f}%")
                    print(f"   Статус: {goal.status}")
                    print(f"   Категория: {goal.category}")
                    if goal.deadline:
                        print(f"   Дедлайн: {goal.deadline}")
                    print("\n--- История изменений ---")
                    for record in goal.history[-10:]:  # последние 10 записей
                        print(f"   {record['date']} - {record['description']}")
                else:
                    print("Неверный номер.")
            except ValueError:
                print("Ошибка ввода.")

    def show_overall_progress(self):
        """Подсчёт общего прогресса по всем целям."""
        if not self.goals:
            print("Нет целей.")
            return

        total_target = sum(g.target_amount for g in self.goals)
        total_balance = sum(g.current_balance for g in self.goals)

        if total_target == 0:
            overall = 100.0
        else:
            overall = (total_balance / total_target) * 100.0

        print(f"\n📈 Общий прогресс по всем целям:")
        print(f"   Итого собрано: {total_balance:.2f} / {total_target:.2f}")
        print(f"   Общий процент выполнения: {overall:.1f}%")

        # Дополнительно: прогресс по категориям
        print("\n--- Прогресс по категориям ---")
        categories_progress = {}
        for goal in self.goals:
            cat = goal.category
            if cat not in categories_progress:
                categories_progress[cat] = {"total": 0, "current": 0}
            categories_progress[cat]["total"] += goal.target_amount
            categories_progress[cat]["current"] += goal.current_balance

        for cat, data in categories_progress.items():
            percent = (data["current"] / data["total"] * 100) if data["total"] > 0 else 0
            print(f"   {cat}: {data['current']:.2f} / {data['total']:.2f} ({percent:.1f}%)")

    def delete_goal(self):
        """Удалить цель."""
        if not self.goals:
            print("Нет целей для удаления.")
            return

        self.list_goals()
        try:
            idx = int(input("Выберите номер цели для удаления: ")) - 1
            if 0 <= idx < len(self.goals):
                removed = self.goals.pop(idx)
                self.save_data()
                print(f"❌ Цель '{removed.name}' удалена.")
            else:
                print("Неверный номер.")
        except ValueError:
            print("Ошибка ввода.")

    def check_reminders(self):
        """Проверить цели на предмет приближения дедлайна (напоминания повышенного уровня)."""
        today = datetime.now().date()
        for goal in self.goals:
            if goal.deadline and goal.status != "выполнена":
                deadline_date = datetime.strptime(goal.deadline, "%Y-%m-%d").date()
                days_left = (deadline_date - today).days
                if 0 <= days_left <= 7:
                    print(
                        f"⏰ Напоминание: цель '{goal.name}' должна быть завершена через {days_left} дней! (Дедлайн: {goal.deadline})")

    def suggest_completion_date(self):
        """Предложить дату завершения цели на основе прогресса и частоты пополнений."""
        if not self.goals:
            print("Нет целей.")
            return

        self.list_goals()
        try:
            idx = int(input("Выберите номер цели для расчета даты завершения: ")) - 1
            if idx < 0 or idx >= len(self.goals):
                print("Неверный номер.")
                return
            goal = self.goals[idx]
        except ValueError:
            print("Ошибка ввода.")
            return

        remaining = goal.target_amount - goal.current_balance
        if remaining <= 0:
            print(f"Цель '{goal.name}' уже выполнена!")
            return

        # Спросить предполагаемую частоту пополнений
        print("\nНа основе истории изменений или введите среднюю частоту пополнений.")
        print("Пример: раз в неделю, раз в месяц и т.д.")
        frequency = input("Частота пополнений (в днях, например 7 для еженедельно): ").strip()

        try:
            days_per_deposit = float(frequency)
            if days_per_deposit <= 0:
                raise ValueError
        except ValueError:
            print("Используем значение по умолчанию: 7 дней (раз в неделю).")
            days_per_deposit = 7.0

        # Предложить среднюю сумму пополнения
        try:
            avg_amount = float(input("Средняя сумма пополнения: "))
            if avg_amount <= 0:
                raise ValueError
        except ValueError:
            print("Не удалось определить среднюю сумму. Расчет невозможен.")
            return

        deposits_needed = remaining / avg_amount
        days_needed = deposits_needed * days_per_deposit

        suggested_date = datetime.now() + timedelta(days=days_needed)
        print(f"📅 При сохранении текущей динамики (пополнения каждые {days_per_deposit} дней по {avg_amount:.2f}),")
        print(f"   цель '{goal.name}' будет достигнута примерно: {suggested_date.strftime('%Y-%m-%d')}")
        print(f"   Осталось пополнений: ~{deposits_needed:.1f}")


# ======================== Главное меню ========================
def main():
    app = PiggyBank()

    while True:
        print("\n" + "=" * 50)
        print("         КОПИЛКА - управление накоплениями")
        print("=" * 50)
        print("1. Добавить цель")
        print("2. Пополнить / снять с цели (изменить баланс)")
        print("3. Просмотреть прогресс")
        print("4. Общий прогресс по всем целям")
        print("5. Удалить цель")
        print("6. Проверить напоминания (дедлайны)")
        print("7. Предложить дату завершения цели")
        print("8. Список всех целей")
        print("9. Выход")
        print("=" * 50)

        choice = input("Ваш выбор: ").strip()

        if choice == "1":
            app.add_goal()
        elif choice == "2":
            app.edit_balance()
        elif choice == "3":
            app.view_progress()
        elif choice == "4":
            app.show_overall_progress()
        elif choice == "5":
            app.delete_goal()
        elif choice == "6":
            app.check_reminders()
        elif choice == "7":
            app.suggest_completion_date()
        elif choice == "8":
            app.list_goals()
        elif choice == "9":
            print("До свидания! Данные сохранены.")
            app.save_data()
            break
        else:
            print("Неверный выбор. Попробуйте снова.")


if __name__ == "__main__":
    main()