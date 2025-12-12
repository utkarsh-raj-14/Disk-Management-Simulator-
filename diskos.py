import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Disk scheduling algorithms and GUI for visualization

def fcfs(requests, head):
    order = [head] + requests[:]
    movement = 0
    for i in range(1, len(order)):
        movement += abs(order[i] - order[i-1])
    return order, movement

def sstf(requests, head):
    reqs = requests[:]
    pos = head
    order = [head]
    movement = 0
    while reqs:
        # find nearest
        nearest = min(reqs, key=lambda x: abs(x - pos))
        movement += abs(nearest - pos)
        pos = nearest
        order.append(pos)
        reqs.remove(nearest)
    return order, movement

def scan(requests, head, disk_size, direction='up'):
    # SCAN (elevator): go in one direction servicing until end, then reverse
    reqs = sorted(requests)
    order = [head]
    movement = 0
    left = [r for r in reqs if r < head]
    right = [r for r in reqs if r >= head]
    if direction == 'up':
        for r in right:
            movement += abs(r - order[-1])
            order.append(r)
        # go to end
        if order[-1] != disk_size - 1:
            movement += abs((disk_size - 1) - order[-1])
            order.append(disk_size - 1)
        # then reverse
        for r in reversed(left):
            movement += abs(order[-1] - r)
            order.append(r)
    else:
        for r in reversed(left):
            movement += abs(r - order[-1])
            order.append(r)
        if order[-1] != 0:
            movement += abs(order[-1] - 0)
            order.append(0)
        for r in right:
            movement += abs(order[-1] - r)
            order.append(r)
    return order, movement

def cscan(requests, head, disk_size, direction='up'):
    # C-SCAN: go in one direction to end, jump to other end (without servicing), continue
    reqs = sorted(requests)
    order = [head]
    movement = 0
    left = [r for r in reqs if r < head]
    right = [r for r in reqs if r >= head]
    if direction == 'up':
        for r in right:
            movement += abs(r - order[-1])
            order.append(r)
        # go to end
        if order[-1] != disk_size - 1:
            movement += abs((disk_size - 1) - order[-1])
            order.append(disk_size - 1)
        # jump to start (no servicing, but count movement or not? usually wrap-around counted)
        # For visualization we will count the jump too (but you can toggle this behavior)
        movement += (disk_size - 1)  # jump from end to start
        order.append(0)
        for r in left:
            movement += abs(r - order[-1])
            order.append(r)
    else:
        for r in reversed(left):
            movement += abs(r - order[-1])
            order.append(r)
        if order[-1] != 0:
            movement += abs(order[-1] - 0)
            order.append(0)
        movement += (disk_size - 1)
        order.append(disk_size - 1)
        for r in reversed(right):
            movement += abs(order[-1] - r)
            order.append(r)
    return order, movement

# Utility to parse requests from user input

def parse_requests(text):
    try:
        parts = text.replace(',', ' ').split()
        reqs = [int(p) for p in parts]
        return reqs
    except ValueError:
        raise

# GUI Application
class DiskSchedulerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Advanced Disk Scheduling Simulator')
        self.geometry('1000x650')
        self.create_widgets()

    def create_widgets(self):
        frm = ttk.Frame(self)
        frm.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        control = ttk.Frame(self)
        control.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)

        # Controls
        ttk.Label(control, text='Disk Size (tracks):').pack(anchor='w')
        self.disk_size_var = tk.IntVar(value=200)
        ttk.Entry(control, textvariable=self.disk_size_var).pack(fill='x')

        ttk.Label(control, text='Initial Head Position:').pack(anchor='w', pady=(8,0))
        self.head_var = tk.IntVar(value=50)
        ttk.Entry(control, textvariable=self.head_var).pack(fill='x')

        ttk.Label(control, text='Requests (comma/space separated):').pack(anchor='w', pady=(8,0))
        self.req_text = tk.Text(control, height=4)
        self.req_text.insert('1.0', '95, 180, 34, 119, 11, 123, 62, 64')
        self.req_text.pack(fill='x')

        ttk.Label(control, text='Algorithm:').pack(anchor='w', pady=(8,0))
        self.algo_var = tk.StringVar(value='FCFS')
        ttk.Combobox(control, textvariable=self.algo_var, values=['FCFS', 'SSTF', 'SCAN', 'C-SCAN']).pack(fill='x')

        ttk.Label(control, text='Direction (for SCAN/C-SCAN):').pack(anchor='w', pady=(8,0))
        self.dir_var = tk.StringVar(value='up')
        ttk.Combobox(control, textvariable=self.dir_var, values=['up', 'down']).pack(fill='x')

        ttk.Button(control, text='Run', command=self.run_simulation).pack(fill='x', pady=(12,4))
        ttk.Button(control, text='Clear Plot', command=self.clear_plot).pack(fill='x', pady=(0,12))

        # Metrics
        self.metrics = tk.Text(control, height=8, state='disabled')
        self.metrics.pack(fill='both', expand=True)

        # Plot area using matplotlib
        self.fig = Figure(figsize=(7,6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel('Sequence Index')
        self.ax.set_ylabel('Track Number')
        self.ax.grid(True)

        self.canvas = FigureCanvasTkAgg(self.fig, master=frm)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)

    def clear_plot(self):
        self.ax.clear()
        self.ax.set_xlabel('Sequence Index')
        self.ax.set_ylabel('Track Number')
        self.ax.grid(True)
        self.canvas.draw()
        self.set_metrics('')

    def set_metrics(self, text):
        self.metrics.configure(state='normal')
        self.metrics.delete('1.0', tk.END)
        self.metrics.insert('1.0', text)
        self.metrics.configure(state='disabled')

    def run_simulation(self):
        try:
            disk_size = int(self.disk_size_var.get())
            head = int(self.head_var.get())
            reqs = parse_requests(self.req_text.get('1.0', tk.END))
            if not reqs:
                messagebox.showerror('Error', 'Please enter at least one request')
                return
            if head < 0 or head >= disk_size:
                messagebox.showerror('Error', 'Head position must be within disk size')
                return
            for r in reqs:
                if r < 0 or r >= disk_size:
                    messagebox.showerror('Error', f'Request {r} out of bounds (0..{disk_size-1})')
                    return
        except Exception as e:
            messagebox.showerror('Error', f'Invalid input: {e}')
            return

        algo = self.algo_var.get()
        direction = self.dir_var.get()

        if algo == 'FCFS':
            order, movement = fcfs(reqs, head)
        elif algo == 'SSTF':
            order, movement = sstf(reqs, head)
        elif algo == 'SCAN':
            order, movement = scan(reqs, head, disk_size, direction=direction)
        elif algo == 'C-SCAN':
            order, movement = cscan(reqs, head, disk_size, direction=direction)
        else:
            messagebox.showerror('Error', 'Unknown algorithm')
            return

        # Metrics
        n_serviced = len(reqs)
        avg_seek = movement / n_serviced if n_serviced else 0
        # Throughput: requests per unit movement (assuming 1 time unit per track movement)
        throughput = n_serviced / movement if movement != 0 else float('inf')

        metrics_text = f"Algorithm: {algo}\n"
        metrics_text += f"Requests: {reqs}\n"
        metrics_text += f"Service Order (including initial head): {order}\n"
        metrics_text += f"Total Head Movement (seek): {movement}\n"
        metrics_text += f"Average Seek per request: {avg_seek:.3f}\n"
        metrics_text += f"Throughput (requests per unit movement): {throughput:.3f}\n"
        self.set_metrics(metrics_text)

        # Plot the head movement
        # x = sequence index, y = track number
        x = list(range(len(order)))
        y = order

        self.ax.clear()
        self.ax.set_title(f'{algo} visualization')
        self.ax.set_xlabel('Sequence Index')
        self.ax.set_ylabel('Track Number')
        self.ax.grid(True)

        # draw lines between consecutive head positions
        self.ax.plot(x, y, marker='o')
        for i in range(1, len(order)):
            self.ax.annotate('', xy=(i, order[i]), xytext=(i-1, order[i-1]),
                             arrowprops=dict(arrowstyle='->'))

        # annotate points with track numbers
        for xi, yi in zip(x, y):
            self.ax.text(xi, yi, f' {yi}', fontsize=8, verticalalignment='bottom')

        # set y limits
        self.ax.set_ylim(-1, disk_size + 1)
        self.canvas.draw()


if __name__ == '__main__':
    app = DiskSchedulerApp()
    app.mainloop()
