```python
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

# 無視するディレクトリやファイルのデフォルトリスト
DEFAULT_EXCLUDE_DIRS = {'.git', '__pycache__', '.vscode', '.idea', 'node_modules', 'venv', '.env'}
DEFAULT_EXCLUDE_FILES = {'.DS_Store', 'Thumbs.db'}

def generate_tree_string(dir_path, prefix="", exclude_dirs=None, exclude_files=None):
    """
    指定されたディレクトリの階層構造を再帰的に走査し、ツリー形式の文字列を生成します。
    """
    if exclude_dirs is None:
        exclude_dirs = DEFAULT_EXCLUDE_DIRS
    if exclude_files is None:
        exclude_files = DEFAULT_EXCLUDE_FILES

    output = []
    
    try:
        # ディレクトリ内のアイテムを取得し、名前順にソート（大文字小文字を区別しない）
        items = sorted(os.listdir(dir_path), key=lambda s: s.lower())
    except PermissionError:
        return [prefix + " [アクセス拒否されたフォルダ]"]
    except Exception as e:
        return [prefix + f" [エラー: {str(e)}]"]

    # フィルタリング（除外対象のディレクトリ・ファイルを除外）
    filtered_items = []
    for item in items:
        full_path = os.path.join(dir_path, item)
        if os.path.isdir(full_path):
            if item in exclude_dirs:
                continue
        else:
            if item in exclude_files:
                continue
        filtered_items.append(item)

    count = len(filtered_items)
    for i, item in enumerate(filtered_items):
        full_path = os.path.join(dir_path, item)
        is_last = (i == count - 1)
        
        # ツリーの枝を表す記号を決定
        connector = "└── " if is_last else "├── "
        
        if os.path.isdir(full_path):
            # ディレクトリの場合
            output.append(f"{prefix}{connector}{item}/")
            # 次の階層のためのインデント（接頭辞）を決定
            next_prefix = prefix + ("    " if is_last else "│   ")
            # 子階層を再帰的に取得して追加
            output.extend(generate_tree_string(full_path, next_prefix, exclude_dirs, exclude_files))
        else:
            # ファイルの場合
            output.append(f"{prefix}{connector}{item}")
            
    return output

class FolderTreeApp:
    """
    フォルダ構成出力ツールのGUIアプリケーションクラスです。
    """
    def __init__(self, root):
        self.root = root
        self.root.title("フォルダ構成テキスト出力ツール")
        self.root.geometry("600x400")
        self.root.minsize(500, 350)
        
        # スタイルの設定
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # メインフレーム
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # タイトルラベル
        title_label = ttk.Label(
            main_frame, 
            text="フォルダ構成テキスト出力ツール", 
            font=("Helvetica", 16, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # 1. フォルダ選択エリア
        select_frame = ttk.LabelFrame(main_frame, text=" 1. 対象のフォルダを選択 ", padding="15")
        select_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.folder_path_var = tk.StringVar(value="フォルダが選択されていません")
        self.folder_label = ttk.Label(
            select_frame, 
            textvariable=self.folder_path_var, 
            wraplength=400,
            foreground="gray"
        )
        self.folder_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        select_btn = ttk.Button(select_frame, text="参照...", command=self.select_folder)
        select_btn.pack(side=tk.RIGHT)
        
        # 2. オプション設定エリア
        options_frame = ttk.LabelFrame(main_frame, text=" 2. オプション設定 ", padding="15")
        options_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 除外設定（チェックボックス）
        self.exclude_var = tk.BooleanVar(value=True)
        exclude_cb = ttk.Checkbutton(
            options_frame, 
            text="システムファイルや一時フォルダを除外する (.git, node_modules, __pycache__ など)", 
            variable=self.exclude_var
        )
        exclude_cb.pack(anchor=tk.W)
        
        # 3. 実行エリア
        self.run_btn = ttk.Button(
            main_frame, 
            text="テキストファイルとして出力・保存", 
            command=self.export_tree,
            state=tk.DISABLED
        )
        self.run_btn.pack(pady=10, ipady=5)
        
        # ステータスバー
        self.status_var = tk.StringVar(value="フォルダを選択してください。")
        status_bar = ttk.Label(
            root, 
            textvariable=self.status_var, 
            relief=tk.SUNKEN, 
            anchor=tk.W, 
            padding=(5, 2)
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def select_folder(self):
        """
        ユーザーにフォルダを選択させ、パスを画面に反映します。
        """
        selected_dir = filedialog.askdirectory(title="解析するフォルダを選択してください")
        if selected_dir:
            self.folder_path_var.set(selected_dir)
            self.folder_label.configure(foreground="black")
            self.run_btn.configure(state=tk.NORMAL)
            self.status_var.set("出力準備完了。出力ボタンを押して保存先を指定してください。")
        else:
            if self.folder_path_var.get() == "フォルダが選択されていません":
                self.run_btn.configure(state=tk.DISABLED)

    def export_tree(self):
        """
        フォルダ構成をテキストファイルに書き出します。
        """
        source_dir = self.folder_path_var.get()
        if not os.path.isdir(source_dir):
            messagebox.showerror("エラー", "有効なフォルダが選択されていません。")
            return
        
        # デフォルトの保存ファイル名を設定
        folder_name = os.path.basename(source_dir)
        if not folder_name:  # ルートディレクトリなどの場合
            folder_name = "root"
        default_filename = f"{folder_name}_structure.txt"
        
        # 保存先ファイルのダイアログを表示
        save_path = filedialog.asksaveasfilename(
            title="保存先テキストファイルを選択",
            initialfile=default_filename,
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        
        if not save_path:
            return  # キャンセルされた場合
            
        try:
            self.status_var.set("フォルダ構成を解析中...")
            self.root.update_idletasks()
            
            # オプションによる除外リストの切り替え
            ex_dirs = DEFAULT_EXCLUDE_DIRS if self.exclude_var.get() else set()
            ex_files = DEFAULT_EXCLUDE_FILES if self.exclude_var.get() else set()
            
            # ツリー構造の構築
            tree_lines = []
            tree_lines.append(f"Directory Structure for: {source_dir}")
            tree_lines.append("=" * 60)
            tree_lines.append(os.path.basename(source_dir) + "/")
            
            # 再帰関数でツリー文字列を取得
            tree_content = generate_tree_string(
                source_dir, 
                prefix="", 
                exclude_dirs=ex_dirs, 
                exclude_files=ex_files
            )
            tree_lines.extend(tree_content)
            
            # ファイルへの書き込み（UTF-8）
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(tree_lines))
                
            self.status_var.set(f"保存完了: {os.path.basename(save_path)}")
            messagebox.showinfo("成功", f"フォルダ構成を正常に出力しました！\n\n保存先:\n{save_path}")
            
        except Exception as e:
            self.status_var.set("エラーが発生しました。")
            messagebox.showerror("エラー", f"ファイルの書き込み中にエラーが発生しました:\n{str(e)}")

if __name__ == "__main__":
    # Tkinterウィンドウの初期化
    root = tk.Tk()
    app = FolderTreeApp(root)
    root.mainloop()

```
eof
### ツールについて
作成した folder_tree_generator.py は、以下の特徴を持っています。
 1. **直感的なGUI操作**:
   黒い画面（CUI）ではなく、使いやすいボタン式のウィンドウが立ち上がります。
 2. **きれいなツリー構造**:
   ├── や └── といった罫線文字を用いて、視覚的にわかりやすいフォルダ階層テキストを自動生成します。
 3. **無駄なファイルの自動除外**:
   .git、node_modules、__pycache__ などのプログラム特有のシステムフォルダや、Macの .DS_Store などの一時ファイルを標準で除外するオプションを搭載しています（チェックボックスで無効にすることも可能です）。
 4. **UTF-8エンコーディング**:
   日本語のファイル名やフォルダ名が含まれていても、文字化けすることなくきれいにテキストファイルへ出力します。
### 実行方法
お使いのパソコンにPythonがインストールされていれば、以下のコマンドで実行できます。
```bash
python folder_tree_generator.py

```
