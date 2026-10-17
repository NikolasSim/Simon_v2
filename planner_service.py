import time
from agent import SimonAgent

def main():
    agent = SimonAgent(use_voice=True, planner=True)
    print("Сервис напоминаний запущен. Ctrl+C — выход.")
    while True:
        try:
            agent.planner.check_and_notify()
        except Exception as e:
            print("Ошибка планировщика:", e)
        time.sleep(5)

if __name__ == "__main__":
    main()
