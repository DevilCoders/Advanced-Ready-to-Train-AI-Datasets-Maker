"""Tkinter based advanced GUI for configuring the dataset maker."""
from __future__ import annotations

from pathlib import Path
from threading import Thread
from tkinter import END, LEFT, RIGHT, BOTH, X, Y, ttk, filedialog, messagebox, scrolledtext
from tkinter import Tk, StringVar, Listbox
from queue import Queue, Empty
from typing import Optional

from .config import CodeSourceConfig, CommandSourceConfig, PipelineConfig
from .pipeline import build_pipeline

LANGUAGE_OPTIONS = [
    ("Python", "python"),
    ("JavaScript", "javascript"),
    ("TypeScript", "typescript"),
    ("Go", "go"),
    ("Perl", "perl"),
    ("PHP", "php"),
    ("Ruby", "ruby"),
    ("Swift", "swift"),
    ("Shell", "shell"),
    ("C", "c"),
    ("C++", "cpp"),
    ("Rust", "rust"),
    ("Kotlin", "kotlin"),
    ("Scala", "scala"),
    ("Objective-C", "objective-c"),
    ("Objective-C++", "objective-c++"),
    ("Dart", "dart"),
    ("Julia", "julia"),
    ("Lua", "lua"),
    ("R", "r"),
    ("SQL", "sql"),
    ("Markdown", "markdown"),
]

SHELL_OPTIONS = [
    "bash",
    "zsh",
    "fish",
    "powershell",
    "pwsh",
    "cmd",
    "sh",
    "ksh",
    "csh",
    "nushell",
    "xonsh",
    "busybox",
]


class DatasetMakerGUI(Tk):
    """High level GUI orchestrator for large-scale scraping configuration."""

    def __init__(self, preload_config: Optional[Path] = None, workspace: Optional[Path] = None) -> None:
        super().__init__()
        self.title("Advanced Ready-to-Train Dataset Builder")
        self.geometry("1280x860")
        self.minsize(960, 720)

        self.root_path = StringVar()
        self.output_path = StringVar()
        self.workspace_path = StringVar(value=str(workspace) if workspace else "")

        self.code_sources: list[CodeSourceConfig] = []
        self.command_sources: list[CommandSourceConfig] = []

        self.log_queue: Queue[str] = Queue()
        self.pipeline_thread: Thread | None = None

        self._build_layout()
        if preload_config:
            self._load_config_from_file(preload_config)

    # Layout helpers -----------------------------------------------------
    def _build_layout(self) -> None:
        self._build_path_frame()
        self._build_code_sources_frame()
        self._build_command_sources_frame()
        self._build_action_frame()
        self.after(200, self._poll_log_queue)

    def _build_path_frame(self) -> None:
        frame = ttk.LabelFrame(self, text="Workspace")
        frame.pack(fill=X, padx=12, pady=8)

        ttk.Label(frame, text="Primary Root:").pack(side=LEFT, padx=4)
        ttk.Entry(frame, textvariable=self.root_path, width=60).pack(side=LEFT, padx=4, fill=X, expand=True)
        ttk.Button(frame, text="Browse", command=self._choose_root).pack(side=LEFT, padx=4)

        ttk.Label(frame, text="Output Directory:").pack(side=LEFT, padx=12)
        ttk.Entry(frame, textvariable=self.output_path, width=50).pack(side=LEFT, padx=4, fill=X, expand=True)
        ttk.Button(frame, text="Browse", command=self._choose_output).pack(side=LEFT, padx=4)

        ttk.Label(frame, text="Workspace:").pack(side=LEFT, padx=12)
        ttk.Entry(frame, textvariable=self.workspace_path, width=40).pack(side=LEFT, padx=4)
        ttk.Button(frame, text="Browse", command=self._choose_workspace).pack(side=LEFT, padx=4)

    def _build_code_sources_frame(self) -> None:
        frame = ttk.LabelFrame(self, text="Code Sources")
        frame.pack(fill=BOTH, padx=12, pady=8, expand=True)

        control_frame = ttk.Frame(frame)
        control_frame.pack(fill=X, pady=4)

        self.code_type_var = StringVar(value="github")
        ttk.Label(control_frame, text="Type").pack(side=LEFT, padx=4)
        ttk.Combobox(control_frame, values=("github", "local"), textvariable=self.code_type_var, width=12).pack(
            side=LEFT, padx=4
        )

        ttk.Label(control_frame, text="Name").pack(side=LEFT, padx=4)
        self.code_name_var = StringVar()
        ttk.Entry(control_frame, textvariable=self.code_name_var, width=18).pack(side=LEFT, padx=4)

        ttk.Label(control_frame, text="Location / URL").pack(side=LEFT, padx=4)
        self.code_location_var = StringVar()
        ttk.Entry(control_frame, textvariable=self.code_location_var, width=40).pack(side=LEFT, padx=4, fill=X, expand=True)

        ttk.Label(control_frame, text="Branch").pack(side=LEFT, padx=4)
        self.code_branch_var = StringVar()
        ttk.Entry(control_frame, textvariable=self.code_branch_var, width=12).pack(side=LEFT, padx=4)

        ttk.Button(control_frame, text="Add Source", command=self._add_code_source).pack(side=LEFT, padx=4)
        ttk.Button(control_frame, text="Remove Selected", command=self._remove_code_source).pack(side=LEFT, padx=4)

        list_frame = ttk.Frame(frame)
        list_frame.pack(fill=BOTH, expand=True)

        columns = ("name", "type", "location", "languages")
        self.code_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=6)
        for col, heading in zip(columns, ["Name", "Type", "Location", "Languages"]):
            self.code_tree.heading(col, text=heading)
            self.code_tree.column(col, width=200 if col != "languages" else 260)
        self.code_tree.pack(side=LEFT, fill=BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.code_tree.yview)
        self.code_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=Y)

        language_frame = ttk.LabelFrame(frame, text="Focus Languages (optional)")
        language_frame.pack(fill=X, pady=6)
        self.language_listbox = Listbox(language_frame, selectmode="multiple", height=6)
        self.language_listbox.pack(fill=X, padx=6, pady=4)
        for label, _ in LANGUAGE_OPTIONS:
            self.language_listbox.insert(END, label)

    def _build_command_sources_frame(self) -> None:
        frame = ttk.LabelFrame(self, text="Terminal Command Sources")
        frame.pack(fill=BOTH, padx=12, pady=8, expand=True)

        control_frame = ttk.Frame(frame)
        control_frame.pack(fill=X, pady=4)

        self.command_type_var = StringVar(value="github")
        ttk.Label(control_frame, text="Type").pack(side=LEFT, padx=4)
        ttk.Combobox(control_frame, values=("github", "local"), textvariable=self.command_type_var, width=12).pack(
            side=LEFT, padx=4
        )

        ttk.Label(control_frame, text="Name").pack(side=LEFT, padx=4)
        self.command_name_var = StringVar()
        ttk.Entry(control_frame, textvariable=self.command_name_var, width=18).pack(side=LEFT, padx=4)

        ttk.Label(control_frame, text="Location / URL").pack(side=LEFT, padx=4)
        self.command_location_var = StringVar()
        ttk.Entry(control_frame, textvariable=self.command_location_var, width=40).pack(
            side=LEFT, padx=4, fill=X, expand=True
        )

        ttk.Button(control_frame, text="Add Commands", command=self._add_command_source).pack(side=LEFT, padx=4)
        ttk.Button(control_frame, text="Remove Selected", command=self._remove_command_source).pack(side=LEFT, padx=4)

        list_frame = ttk.Frame(frame)
        list_frame.pack(fill=BOTH, expand=True)
        columns = ("name", "type", "location", "shells")
        self.command_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=6)
        for col, heading in zip(columns, ["Name", "Type", "Location", "Shell families"]):
            self.command_tree.heading(col, text=heading)
            self.command_tree.column(col, width=200 if col != "shells" else 260)
        self.command_tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.command_tree.yview)
        self.command_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=Y)

        shell_frame = ttk.LabelFrame(frame, text="Target Shell Families")
        shell_frame.pack(fill=X, pady=6)
        self.shell_listbox = Listbox(shell_frame, selectmode="multiple", height=6)
        self.shell_listbox.pack(fill=X, padx=6, pady=4)
        for shell in SHELL_OPTIONS:
            self.shell_listbox.insert(END, shell)

    def _build_action_frame(self) -> None:
        frame = ttk.LabelFrame(self, text="Execution")
        frame.pack(fill=BOTH, padx=12, pady=8, expand=True)

        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=X)

        ttk.Button(button_frame, text="Load Config", command=self._prompt_and_load_config).pack(side=LEFT, padx=4)
        self.run_button = ttk.Button(button_frame, text="Run Pipeline", command=self._start_pipeline)
        self.run_button.pack(side=LEFT, padx=4)
        ttk.Button(button_frame, text="Stop", command=self._stop_pipeline).pack(side=LEFT, padx=4)

        self.log_widget = scrolledtext.ScrolledText(frame, height=14, state="disabled")
        self.log_widget.pack(fill=BOTH, expand=True, padx=4, pady=6)

    # Path selection helpers ---------------------------------------------
    def _choose_root(self) -> None:
        path = filedialog.askdirectory(title="Select repository root")
        if path:
            self.root_path.set(path)

    def _choose_output(self) -> None:
        path = filedialog.askdirectory(title="Select output directory")
        if path:
            self.output_path.set(path)

    def _choose_workspace(self) -> None:
        path = filedialog.askdirectory(title="Select workspace for remote sources")
        if path:
            self.workspace_path.set(path)

    # Source management --------------------------------------------------
    def _selected_languages(self) -> tuple[str, ...]:
        selections = self.language_listbox.curselection()
        if not selections:
            return ()
        return tuple(LANGUAGE_OPTIONS[idx][1] for idx in selections)

    def _add_code_source(self) -> None:
        location = self.code_location_var.get().strip()
        if not location:
            messagebox.showerror("Missing information", "A repository location or path is required")
            return
        name = self.code_name_var.get().strip() or location.split("/")[-1]
        languages = self._selected_languages()
        code_source = CodeSourceConfig(
            name=name,
            type=self.code_type_var.get(),
            location=location,
            branch=self.code_branch_var.get().strip() or None,
            languages=languages,
        )
        self.code_sources.append(code_source)
        self.code_tree.insert("", END, values=(code_source.name, code_source.type, code_source.location, ", ".join(code_source.languages)))
        self._log(f"Added code source: {code_source.name}")
        self.code_location_var.set("")
        self.code_name_var.set("")
        self.code_branch_var.set("")

    def _remove_code_source(self) -> None:
        selected = self.code_tree.selection()
        if not selected:
            return
        entries = sorted(((self.code_tree.index(item), item) for item in selected), reverse=True)
        for index, item in entries:
            removed = self.code_sources.pop(index)
            self.code_tree.delete(item)
            self._log(f"Removed code source: {removed.name}")

    def _selected_shells(self) -> tuple[str, ...]:
        selections = self.shell_listbox.curselection()
        if not selections:
            return tuple(SHELL_OPTIONS)
        return tuple(SHELL_OPTIONS[idx] for idx in selections)

    def _add_command_source(self) -> None:
        location = self.command_location_var.get().strip()
        if not location:
            messagebox.showerror("Missing information", "A repository location or path is required")
            return
        name = self.command_name_var.get().strip() or location.split("/")[-1]
        shells = self._selected_shells()
        command_source = CommandSourceConfig(
            name=name,
            type=self.command_type_var.get(),
            location=location,
            shells=shells,
        )
        self.command_sources.append(command_source)
        self.command_tree.insert(
            "",
            END,
            values=(command_source.name, command_source.type, command_source.location, ", ".join(command_source.shells)),
        )
        self._log(f"Added command source: {command_source.name}")
        self.command_location_var.set("")
        self.command_name_var.set("")

    def _remove_command_source(self) -> None:
        selected = self.command_tree.selection()
        if not selected:
            return
        entries = sorted(((self.command_tree.index(item), item) for item in selected), reverse=True)
        for index, item in entries:
            removed = self.command_sources.pop(index)
            self.command_tree.delete(item)
            self._log(f"Removed command source: {removed.name}")

    # Config loading -----------------------------------------------------
    def _prompt_and_load_config(self) -> None:
        path = filedialog.askopenfilename(
            title="Select dataset configuration",
            filetypes=[("YAML", "*.yml *.yaml"), ("JSON", "*.json")],
        )
        if path:
            self._load_config_from_file(Path(path))

    def _load_config_from_file(self, path: Path) -> None:
        try:
            config = PipelineConfig.load(path)
        except Exception as exc:  # pragma: no cover - user interaction
            messagebox.showerror("Failed to load configuration", str(exc))
            return

        self.root_path.set(str(config.root))
        self.output_path.set(str(config.output_dir))
        if config.workspace:
            self.workspace_path.set(str(config.workspace))
        else:
            self.workspace_path.set("")

        self.code_sources = list(config.code_sources)
        self.command_sources = list(config.command_sources)

        for tree in (self.code_tree, self.command_tree):
            for item in tree.get_children():
                tree.delete(item)

        for source in self.code_sources:
            self.code_tree.insert("", END, values=(source.name, source.type, source.location, ", ".join(source.languages)))
        for source in self.command_sources:
            self.command_tree.insert(
                "",
                END,
                values=(source.name, source.type, source.location, ", ".join(source.shells)),
            )
        self._log(f"Loaded configuration from {path}")

    # Pipeline execution -------------------------------------------------
    def _start_pipeline(self) -> None:
        if self.pipeline_thread and self.pipeline_thread.is_alive():
            messagebox.showinfo("Pipeline running", "A pipeline run is already in progress")
            return
        if not self.output_path.get():
            messagebox.showerror("Missing output", "Please select an output directory")
            return

        root_input = self.root_path.get().strip()
        config = PipelineConfig(
            root=Path(root_input) if root_input else Path.cwd(),
            output_dir=Path(self.output_path.get()),
            code_sources=tuple(self.code_sources),
            command_sources=tuple(self.command_sources),
            workspace=Path(self.workspace_path.get()) if self.workspace_path.get() else None,
        )
        try:
            config.validate()
        except Exception as exc:
            messagebox.showerror("Invalid configuration", str(exc))
            return

        self.run_button.state(["disabled"])
        self._log("Starting pipeline run...")
        self.pipeline_thread = Thread(target=self._run_pipeline, args=(config,), daemon=True)
        self.pipeline_thread.start()

    def _run_pipeline(self, config: PipelineConfig) -> None:
        try:
            stats = build_pipeline(config)
        except Exception as exc:  # pragma: no cover - GUI threading
            self.log_queue.put(f"ERROR: {exc}")
        else:
            self.log_queue.put(stats.format_summary())
        finally:
            self.log_queue.put("__COMPLETE__")

    def _stop_pipeline(self) -> None:
        if self.pipeline_thread and self.pipeline_thread.is_alive():
            self._log("Stopping pipeline is not supported mid-flight; please wait for completion.")
        else:
            self._log("No active pipeline run.")

    def _poll_log_queue(self) -> None:
        try:
            while True:
                message = self.log_queue.get_nowait()
                if message == "__COMPLETE__":
                    self.run_button.state(["!disabled"])
                    self.pipeline_thread = None
                    continue
                self._log(message)
        except Empty:
            pass
        finally:
            self.after(250, self._poll_log_queue)

    def _log(self, message: str) -> None:
        self.log_widget.configure(state="normal")
        self.log_widget.insert(END, f"{message}\n")
        self.log_widget.configure(state="disabled")
        self.log_widget.see(END)


def launch() -> None:
    app = DatasetMakerGUI()
    app.mainloop()
