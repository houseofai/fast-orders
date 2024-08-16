import tkinter as tk
from tkinter import messagebox

import winsound

from orders import MyOrder, IBConnection
from util import get_time


def custom_confirmation_popup(myOrder):
    symbol = myOrder.contract.symbol
    action = myOrder.action
    position = myOrder.position

    limit_price = myOrder.limit_price
    total_quantity = myOrder.total_quantity
    invested_amount = myOrder.invested_amount
    account_cash = myOrder.account_cash

    latest_price = myOrder.latest_price
    stop_loss = myOrder.stop_loss
    stop_loss_percentage = myOrder.stop_loss_percentage

    popup = tk.Toplevel()
    popup.title("Confirm Order")

    bold_font = ('Helvetica', 12, 'bold')
    bold_green_font = ('Helvetica', 12, 'bold')
    bold_red_font = ('Helvetica', 12, 'bold')

    # Create a main frame
    main_frame = tk.Frame(popup, padx=20, pady=20)
    main_frame.pack(fill='both', expand=True)

    # Add header with highlighted symbol
    header_frame = tk.Frame(main_frame)
    header_frame.pack(pady=10)

    tk.Label(header_frame, text=f"Confirm ", font=('Helvetica', 14, 'bold')).pack(side="left")
    tk.Label(header_frame, text=f"{action} {symbol}", font=('Helvetica', 14, 'bold'),
             fg="green" if action == "BUY" else "red").pack(side="left")
    tk.Label(header_frame, text=" order", font=('Helvetica', 14, 'bold')).pack(side="left")

    # Create a frame for the main information
    info_frame = tk.Frame(main_frame)
    info_frame.pack(pady=10)

    # Add the main information labels
    # tk.Label(info_frame, text=f"Exchange: {exchange} | Symbol: {symbol}", font=bold_font).grid(row=0, column=0,
    #                                                                                           sticky='w', pady=5)
    tk.Label(info_frame, text=f"Limit Price: ${limit_price:.2f}", font=bold_green_font, fg="green").grid(row=0,
                                                                                                         column=0,
                                                                                                         pady=5)
    tk.Label(info_frame, text=f"Latest Price: ${latest_price:.2f}", ).grid(row=1, column=0, pady=5)
    tk.Label(info_frame, text=f"Quantity: {total_quantity} shares ({position})", font=bold_font, fg="red").grid(row=2,
                                                                                                                column=0,
                                                                                                                sticky='w',
                                                                                                                pady=5)
    tk.Label(info_frame, text=f"Total Amount Invested: ${invested_amount:.2f}", font=bold_red_font, fg="red").grid(
        row=3, column=0, sticky='w', pady=5)

    # Create a frame for the additional information
    additional_frame = tk.Frame(main_frame)
    additional_frame.pack(pady=10)

    # Add the additional information labels
    tk.Label(additional_frame, text=f"Account Dollar: ${account_cash:.2f}", font=('Helvetica', 10)).grid(row=0,
                                                                                                         column=0,
                                                                                                         sticky='w',
                                                                                                         pady=2)
    tk.Label(additional_frame, text=f"Risk: ${myOrder.dollar_risk} | Threshold: ${myOrder.dollar_threshold}",
             font=('Helvetica', 10)).grid(row=1, column=0, sticky='w', pady=2)
    tk.Label(additional_frame, text=f"Latest Price: ${latest_price:.2f}", font=('Helvetica', 10)).grid(row=2, column=0,
                                                                                                       sticky='w',
                                                                                                       pady=2)
    tk.Label(additional_frame, text=f"Stop Loss: ${stop_loss:.2f} ({stop_loss_percentage:.2f}%)",
             font=('Helvetica', 10)).grid(row=3, column=0, sticky='w', pady=2)

    # Add the confirmation question
    tk.Label(main_frame, text="Do you want to place this order?", font=('Helvetica', 10)).pack(pady=10)

    # Create a frame for the buttons
    btn_frame = tk.Frame(main_frame)
    btn_frame.pack(pady=10)

    def on_confirm():
        winsound.Beep(1000, 500)  # Frequency: 1000 Hz, Duration: 500 ms
        # playsound('sounds/partout_par_terre.mp3')  # Path to your custom sound file
        popup.destroy()
        popup.result = True

    def on_cancel():
        popup.destroy()
        popup.result = False

    # Add buttons to the button frame
    tk.Button(btn_frame, text="Yes", command=on_confirm, width=10).pack(side="left", padx=10)
    tk.Button(btn_frame, text="No", command=on_cancel, width=10).pack(side="right", padx=10)

    # Set focus and grab
    popup.grab_set()
    popup.wait_window()
    return getattr(popup, 'result', False)


def create_gui():
    root = tk.Tk()
    root.title("Trading Order Placement")

    # Set a consistent font for all labels and entries
    label_font = ('Helvetica', 10)
    entry_font = ('Helvetica', 10)

    # Create a main frame
    main_frame = tk.Frame(root, padx=20, pady=20)
    main_frame.pack(fill='both', expand=True)

    # Add a header label
    header_label = tk.Label(main_frame, text="Trading Order Placement", font=('Helvetica', 14, 'bold'))
    header_label.grid(row=0, column=0, columnspan=2, pady=10)

    # Create and place labels and entry widgets
    tk.Label(main_frame, text="Action", font=label_font).grid(row=1, column=0, sticky='e', pady=5, padx=5)
    tk.Label(main_frame, text="Position", font=label_font).grid(row=2, column=0, sticky='e', pady=5, padx=5)
    tk.Label(main_frame, text="Symbol", font=label_font).grid(row=3, column=0, sticky='e', pady=5, padx=5)
    tk.Label(main_frame, text="Stop Loss", font=label_font).grid(row=4, column=0, sticky='e', pady=5, padx=5)

    tk.Label(main_frame, text="Dollar Risk", font=label_font).grid(row=5, column=0, sticky='e', pady=5, padx=5)
    tk.Label(main_frame, text="Dollar Threshold", font=label_font).grid(row=6, column=0, sticky='e', pady=5, padx=5)

    action_var = tk.StringVar(value="BUY")
    dollar_risk_var = tk.DoubleVar(value=50)  # Default value for dollar risk
    dollar_threshold_var = tk.DoubleVar(value=10000)  # Default value for dollar threshold

    def highlight_button(action):
        if action == "BUY":
            buy_button.config(bg="green", fg="white")
            sell_button.config(bg="SystemButtonFace", fg="black")
        else:
            sell_button.config(bg="red", fg="white")
            buy_button.config(bg="SystemButtonFace", fg="black")

    def set_action(action):
        action_var.set(action)
        highlight_button(action)

    buy_button = tk.Button(main_frame, text="BUY", command=lambda: set_action("BUY"), font=label_font, width=10)
    sell_button = tk.Button(main_frame, text="SELL", command=lambda: set_action("SELL"), font=label_font, width=10)
    buy_button.grid(row=1, column=1, sticky='w', pady=5)
    sell_button.grid(row=1, column=2, sticky='w', pady=5)
    highlight_button("BUY")  # Set initial highlight

    position_values = {"Full": 1, "Half": 0.5, "Quarter": 0.25}
    position_var = tk.StringVar(value="Full")

    def highlight_position_button(position):
        full_button.config(bg="SystemButtonFace", fg="black")
        half_button.config(bg="SystemButtonFace", fg="black")
        quarter_button.config(bg="SystemButtonFace", fg="black")
        if position == "Full":
            full_button.config(bg="blue", fg="white")
        elif position == "Half":
            half_button.config(bg="blue", fg="white")
        else:
            quarter_button.config(bg="blue", fg="white")

    def set_position(position):
        position_var.set(position)
        highlight_position_button(position)

    full_button = tk.Button(main_frame, text="Full", command=lambda: set_position("Full"), font=label_font, width=10)
    half_button = tk.Button(main_frame, text="Half", command=lambda: set_position("Half"), font=label_font, width=10)
    quarter_button = tk.Button(main_frame, text="Quarter", command=lambda: set_position("Quarter"), font=label_font,
                               width=10)
    full_button.grid(row=2, column=1, sticky='w', pady=5)
    half_button.grid(row=2, column=2, sticky='w', pady=5)
    quarter_button.grid(row=2, column=3, sticky='w', pady=5)
    highlight_position_button("Full")  # Set initial highlight

    symbol_entry = tk.Entry(main_frame, font=entry_font)
    stop_loss_entry = tk.Entry(main_frame, font=entry_font)
    dollar_risk_entry = tk.Entry(main_frame, font=entry_font, textvariable=dollar_risk_var)
    dollar_threshold_entry = tk.Entry(main_frame, font=entry_font, textvariable=dollar_threshold_var)

    symbol_entry.grid(row=3, column=1, sticky='w', pady=5)
    symbol_entry.focus()
    stop_loss_entry.grid(row=4, column=1, sticky='w', pady=5)
    dollar_risk_entry.grid(row=5, column=1, sticky='w', pady=5)
    dollar_threshold_entry.grid(row=6, column=1, sticky='w', pady=5)

    connection = IBConnection()

    def on_submit(event=None):
        symbol = symbol_entry.get().upper()
        position = position_values[position_var.get()]
        action = action_var.get()
        stop_loss = stop_loss_entry.get()
        dollar_risk = dollar_risk_var.get()
        dollar_threshold = dollar_threshold_var.get()

        myOrder = MyOrder(connection, dollar_risk, dollar_threshold)

        try:
            myOrder.prep_order(symbol, position, action, stop_loss)
        except ValueError as e:
            messagebox.showerror(e.args[0], e.args[1])
            return

        confirmation = custom_confirmation_popup(myOrder)

        if not confirmation:
            print(f"[{get_time()}] Order not confirmed. Exiting.")
            return
        else:
            print(f"[{get_time()}] Placing order...")
            myOrder.place_order()
            print(f"[{get_time()}] Order placed successfully.")

    def on_reset():
        symbol_entry.delete(0, tk.END)
        position_var.set("Full")
        action_var.set("BUY")
        stop_loss_entry.delete(0, tk.END)
        highlight_button("BUY")
        highlight_position_button("Full")

    def on_exit():
        connection.disconnect()
        root.destroy()

    # Create and place Submit and Reset buttons
    submit_button = tk.Button(main_frame, text="Submit", command=on_submit, font=label_font, width=10)
    reset_button = tk.Button(main_frame, text="Reset", command=on_reset, font=label_font, width=10)

    submit_button.grid(row=7, column=0, pady=20)
    reset_button.grid(row=7, column=1, pady=20)

    root.bind('<Return>', on_submit)
    root.protocol("WM_DELETE_WINDOW", on_exit)
    root.mainloop()


if __name__ == '__main__':
    create_gui()
