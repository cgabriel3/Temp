import pyautogui as pg


def type_custom_text(text, repeat):
  pg.sleep(3)
  for i in range(repeat):
    print(f"Loop {i}/{repeat - 1}")  # Print loop count
    pg.write(text)
    pg.press("enter")


custom_text = input("Enter the custom text: ")
repeat_times = int(input("Enter the number of times to repeat: "))

type_custom_text(custom_text, repeat_times)
