import pyautogui

print(pyautogui.size())

def enter_invoice(invoice):
    pyautogui.hotkey('ctrl', 'tab')
    pyautogui.write(invoice.date)
    pyautogui.press('tab')
    pyautogui.write(invoice.number)
    pyautogui.press('down', presses=2)
    # pyautogui.press('down')
    pyautogui.write(invoice.amount)
    pyautogui.press('down', presses=3)
    # pyautogui.press('down')
    # pyautogui.press('down')
    pyautogui.press('tab')
    pyautogui.write(invoice.workorder)
    pyautogui.press('enter')

