from __future__ import annotations

from pathlib import Path
from queue import Empty, Queue
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from src.application.commands import CancelParseCommand, StartParseCommand
from src.application.controller import AppController
from src.domain.events import ProgressEvent, ProgressEventType


class MainWindow:
    POLL_MS = 100

    def __init__(self, controller: AppController, progress_queue: Queue) -> None:
        self._controller = controller
        self._progress_queue = progress_queue
        self._root = tk.Tk()
        self._root.title("Atlas Parser v3")
        self._root.geometry("1260x760")
        self._root.minsize(1100, 680)

        self._start_command = StartParseCommand(controller)
        self._cancel_command = CancelParseCommand(controller)

        self._output_var = tk.StringVar()
        self._status_var = tk.StringVar(value="대기 중")
        self._current_set_var = tk.StringVar(value="-")
        self._current_atlas_var = tk.StringVar(value="-")
        self._current_output_var = tk.StringVar(value="-")
        self._progress_text_var = tk.StringVar(value="0 / 0")

        self._build_ui()
        self._set_running_state(False)
        self._schedule_queue_poll()

    def run(self) -> None:
        self._root.mainloop()

    def _build_ui(self) -> None:
        self._root.columnconfigure(0, weight=1)
        self._root.rowconfigure(1, weight=1)

        top = ttk.Frame(self._root, padding=12)
        top.grid(row=0, column=0, sticky="ew")
        top.columnconfigure(1, weight=1)

        ttk.Label(top, text="출력 폴더").grid(row=0, column=0, sticky="w", padx=(0, 8))
        output_entry = ttk.Entry(top, textvariable=self._output_var)
        output_entry.grid(row=0, column=1, sticky="ew")
        ttk.Button(top, text="폴더 선택", command=self._choose_output_dir).grid(row=0, column=2, padx=(8, 0))

        middle = ttk.Frame(self._root, padding=(12, 0, 12, 0))
        middle.grid(row=1, column=0, sticky="nsew")
        middle.columnconfigure(0, weight=1)
        middle.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(middle)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        self._add_folder_button = ttk.Button(toolbar, text="폴더 세트 추가", command=self._add_folder_set)
        self._add_folder_button.pack(side="left")
        self._add_manual_button = ttk.Button(toolbar, text="수동 세트 추가", command=self._add_manual_set)
        self._add_manual_button.pack(side="left", padx=6)
        self._remove_button = ttk.Button(toolbar, text="선택 삭제", command=self._remove_selected_set)
        self._remove_button.pack(side="left")
        self._clear_button = ttk.Button(toolbar, text="전체 삭제", command=self._clear_sets)
        self._clear_button.pack(side="left", padx=(6, 0))
        self._start_button = ttk.Button(toolbar, text="파싱 시작", command=self._on_start)
        self._start_button.pack(side="right")
        self._cancel_button = ttk.Button(toolbar, text="취소", command=self._on_cancel)
        self._cancel_button.pack(side="right", padx=(0, 6))

        help_text = (
            "세트 기준: PNG 여러 장 + SpriteInfo.json 한 장이 있는 폴더 1개\n"
            "추천: '폴더 세트 추가' 사용"
        )
        ttk.Label(middle, text=help_text, foreground="#666666").grid(row=2, column=0, sticky="w", pady=(8, 0))

        columns = ("name", "atlas_count", "folder", "json")
        self._tree = ttk.Treeview(middle, columns=columns, show="headings", height=16)
        self._tree.grid(row=1, column=0, sticky="nsew")
        self._tree.heading("name", text="세트 이름")
        self._tree.heading("atlas_count", text="PNG 수")
        self._tree.heading("folder", text="세트 폴더")
        self._tree.heading("json", text="SpriteInfo.json")
        self._tree.column("name", width=180, anchor="w")
        self._tree.column("atlas_count", width=90, anchor="center")
        self._tree.column("folder", width=470, anchor="w")
        self._tree.column("json", width=430, anchor="w")

        scroll_y = ttk.Scrollbar(middle, orient="vertical", command=self._tree.yview)
        scroll_y.grid(row=1, column=1, sticky="ns")
        self._tree.configure(yscrollcommand=scroll_y.set)

        bottom = ttk.LabelFrame(self._root, text="진행 상태", padding=12)
        bottom.grid(row=2, column=0, sticky="ew", padx=12, pady=12)
        bottom.columnconfigure(1, weight=1)

        ttk.Label(bottom, text="상태").grid(row=0, column=0, sticky="nw", padx=(0, 8))
        ttk.Label(bottom, textvariable=self._status_var).grid(row=0, column=1, sticky="nw")

        ttk.Label(bottom, text="현재 세트").grid(row=1, column=0, sticky="nw", padx=(0, 8), pady=(6, 0))
        ttk.Label(bottom, textvariable=self._current_set_var).grid(row=1, column=1, sticky="nw", pady=(6, 0))

        ttk.Label(bottom, text="현재 아틀라스").grid(row=2, column=0, sticky="nw", padx=(0, 8), pady=(6, 0))
        ttk.Label(bottom, textvariable=self._current_atlas_var).grid(row=2, column=1, sticky="nw", pady=(6, 0))

        ttk.Label(bottom, text="현재 파일").grid(row=3, column=0, sticky="nw", padx=(0, 8), pady=(6, 0))
        ttk.Label(bottom, textvariable=self._current_output_var, wraplength=980).grid(row=3, column=1, sticky="nw", pady=(6, 0))

        self._progress = ttk.Progressbar(bottom, mode="determinate")
        self._progress.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        ttk.Label(bottom, textvariable=self._progress_text_var).grid(row=5, column=0, columnspan=2, sticky="e", pady=(6, 0))

    def _choose_output_dir(self) -> None:
        directory = filedialog.askdirectory(title="출력 폴더 선택")
        if not directory:
            return

        try:
            self._controller.set_output_dir(directory)
            self._output_var.set(directory)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("오류", str(exc), parent=self._root)

    def _add_folder_set(self) -> None:
        folder = filedialog.askdirectory(title="PNG 여러 장 + SpriteInfo.json 이 들어있는 폴더 선택")
        if not folder:
            return

        try:
            atlas_set = self._controller.add_set_from_folder(folder)
            self._insert_set_row(atlas_set)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("오류", str(exc), parent=self._root)

    def _add_manual_set(self) -> None:
        atlas_paths = filedialog.askopenfilenames(
            title="세트에 포함할 PNG 파일 여러 개 선택",
            filetypes=[("PNG image", "*.png"), ("All files", "*.*")],
        )
        if not atlas_paths:
            return

        initial_dir = str(Path(atlas_paths[0]).parent)
        json_path = filedialog.askopenfilename(
            title="SpriteInfo.json 선택",
            initialdir=initial_dir,
            filetypes=[("JSON file", "*.json"), ("All files", "*.*")],
        )
        if not json_path:
            return

        try:
            atlas_set = self._controller.add_set_from_files(atlas_paths, json_path)
            self._insert_set_row(atlas_set)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("오류", str(exc), parent=self._root)

    def _insert_set_row(self, atlas_set) -> None:
        self._tree.insert(
            "",
            "end",
            iid=atlas_set.id,
            values=(
                atlas_set.display_name,
                len(atlas_set.atlas_paths),
                str(atlas_set.source_dir),
                str(atlas_set.info_path),
            ),
        )

    def _remove_selected_set(self) -> None:
        selection = self._tree.selection()
        if not selection:
            messagebox.showinfo("안내", "삭제할 세트를 먼저 선택하세요.", parent=self._root)
            return

        for item_id in selection:
            self._controller.remove_set(item_id)
            self._tree.delete(item_id)

    def _clear_sets(self) -> None:
        if self._controller.is_running:
            messagebox.showwarning("경고", "파싱 중에는 전체 삭제할 수 없습니다.", parent=self._root)
            return

        self._controller.clear_sets()
        for item in self._tree.get_children():
            self._tree.delete(item)

    def _on_start(self) -> None:
        try:
            if self._output_var.get().strip():
                self._controller.set_output_dir(self._output_var.get().strip())
            self._start_command.execute()
            self._status_var.set("파싱 시작...")
            self._current_atlas_var.set("-")
            self._current_output_var.set("-")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("오류", str(exc), parent=self._root)

    def _on_cancel(self) -> None:
        if not self._controller.is_running:
            messagebox.showinfo("안내", "현재 실행 중인 작업이 없습니다.", parent=self._root)
            return
        self._cancel_command.execute()
        self._status_var.set("취소 요청 중...")

    def _schedule_queue_poll(self) -> None:
        self._poll_progress_queue()
        self._root.after(self.POLL_MS, self._schedule_queue_poll)

    def _poll_progress_queue(self) -> None:
        while True:
            try:
                event: ProgressEvent = self._progress_queue.get_nowait()
            except Empty:
                break
            self._apply_event(event)

    def _apply_event(self, event: ProgressEvent) -> None:
        self._status_var.set(event.message)

        if event.total:
            self._progress.configure(maximum=event.total)
            self._progress["value"] = event.current
            self._progress_text_var.set(f"{event.current} / {event.total}")
        else:
            self._progress.configure(maximum=1)
            self._progress["value"] = 0
            self._progress_text_var.set("0 / 0")

        if event.set_name:
            self._current_set_var.set(event.set_name)
        if event.current_atlas:
            self._current_atlas_var.set(event.current_atlas)
        if event.current_output:
            self._current_output_var.set(event.current_output)

        if event.event_type == ProgressEventType.STARTED:
            self._set_running_state(True)
        elif event.event_type == ProgressEventType.RECORD_SAVED:
            self._highlight_current_set(event.set_name)
        elif event.event_type == ProgressEventType.SET_COMPLETED:
            self._mark_set_completed(event.set_name)
        elif event.event_type == ProgressEventType.COMPLETED:
            self._set_running_state(False)
            self._current_output_var.set(str(event.output_dir) if event.output_dir else "-")
            messagebox.showinfo("완료", event.message, parent=self._root)
        elif event.event_type == ProgressEventType.CANCELLED:
            self._set_running_state(False)
            messagebox.showinfo("취소", event.message, parent=self._root)
        elif event.event_type == ProgressEventType.ERROR:
            self._set_running_state(False)
            messagebox.showerror("오류", event.error_message or event.message, parent=self._root)

    def _set_running_state(self, running: bool) -> None:
        state_add = "disabled" if running else "normal"
        self._add_folder_button.configure(state=state_add)
        self._add_manual_button.configure(state=state_add)
        self._remove_button.configure(state=state_add)
        self._clear_button.configure(state=state_add)
        self._start_button.configure(state="disabled" if running else "normal")
        self._cancel_button.configure(state="normal" if running else "disabled")
        self._tree.configure(selectmode="none" if running else "extended")

    def _highlight_current_set(self, set_name: str) -> None:
        for item_id in self._tree.get_children():
            values = self._tree.item(item_id, "values")
            if values and values[0] == set_name:
                self._tree.selection_set(item_id)
                self._tree.focus(item_id)
                self._tree.see(item_id)
                break

    def _mark_set_completed(self, set_name: str) -> None:
        self._highlight_current_set(set_name)
