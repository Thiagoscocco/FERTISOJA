# Guia de Design de Interface - Easy IOP Style
## Template para Implementação em Outros Softwares

### 🎨 **Paleta de Cores Padrão**

#### **Cores Primárias**
```python

# INTERPRETE ESSA PALETA DE CORES PORÉM LEVE EM CONSIDERAÇÃO QUE O SOFTWARE PODE NÃO NECESSITAR DE SOLO, PALHA E PLANTAS, UTILIZE ELAS PARA AS PARTES DO SOFTWARE QUE NÃO NECESSÁRIAMENTE TENHAM A VER COM AS MESMAS. USE DE IDEIA E ADAPTE PARA A SITUAÇAÕ PEDIDA. 
# Cores dos Botões
PLANT_COLOR = "#4CAF50"        # Verde para plantas
PLANT_HOVER = "#388E3C"        # Verde escuro hover
STRAW_COLOR = "#FF9800"        # Laranja para palha
STRAW_HOVER = "#E65100"        # Laranja escuro hover
SOIL_COLOR = "#795548"         # Marrom para solo
SOIL_HOVER = "#5D4037"         # Marrom escuro hover

# Cores de Ação
PRIMARY_BLUE = "#2196F3"       # Azul principal
PRIMARY_HOVER = "#1976D2"      # Azul hover
SUCCESS_GREEN = "#4CAF50"      # Verde sucesso
WARNING_ORANGE = "#FF9800"     # Laranja aviso
DANGER_RED = "#F44336"         # Vermelho perigo

# Cores de Interface
BACKGROUND_LIGHT = "#f8f9fa"   # Fundo claro
BACKGROUND_DARK = "#2b2b2b"    # Fundo escuro
PANEL_LIGHT = "#ffffff"        # Painel claro
PANEL_DARK = "#3a3a3a"         # Painel escuro
TEXT_PRIMARY = "#1f538d"       # Texto primário
TEXT_SECONDARY = "#666666"     # Texto secundário
```

#### **Cores de Sliders**
```python
SLIDER_PLANT = "#4CAF50"       # Verde plantas
SLIDER_PLANT_BTN = "#2E7D32"   # Botão slider plantas
SLIDER_STRAW = "#FF9800"       # Laranja palha
SLIDER_STRAW_BTN = "#F57C00"   # Botão slider palha
```

### 🏗️ **Estrutura de Layout Padrão**

#### **Grid System**
```python
# Configuração de Grid Principal
self.rowconfigure(0, weight=0)      # Toolbar superior
self.rowconfigure(1, weight=0)      # Barra de progresso
self.rowconfigure(2, weight=1)      # Área principal
self.columnconfigure(0, weight=1)   # Coluna principal

# Configuração de Toolbar
toolbar.columnconfigure(0, weight=0)  # Botão 1
toolbar.columnconfigure(1, weight=0)  # Botão 2
toolbar.columnconfigure(2, weight=0)  # Botão 3
toolbar.columnconfigure(3, weight=1)  # Espaçador
toolbar.columnconfigure(4, weight=0)  # Dropdown/Controles
```

#### **Estrutura de Painéis**
```python
# Painel Principal
main_frame = ctk.CTkFrame(self, fg_color=("#f8f9fa", "#2b2b2b"))
main_frame.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)

# Painel de Controles
controls_frame = ctk.CTkFrame(panel, fg_color=("#ffffff", "#3a3a3a"))
controls_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
```

### 🔘 **Padrões de Botões**

#### **Botões Principais**
```python
# Botão de Ação Principal
btn_primary = ctk.CTkButton(
    parent, 
    text="📁 CARREGAR IMAGEM…",  # Emoji + texto em maiúsculo
    command=self._on_action,
    fg_color=PRIMARY_BLUE, 
    hover_color=PRIMARY_HOVER,
    font=ctk.CTkFont(size=14, weight="bold"),
    height=40
)

# Botão de Processamento
btn_process = ctk.CTkButton(
    parent, 
    text="⚡ PROCESSAR",  # Emoji + texto em maiúsculo
    command=self._on_process,
    fg_color=SUCCESS_GREEN, 
    hover_color=PLANT_HOVER,
    font=ctk.CTkFont(size=14, weight="bold"),
    height=40
)
```

#### **Botões de Controle**
```python
# Botão SET/UNSET
btn_set = ctk.CTkButton(
    parent, 
    text="SET", 
    width=50, 
    height=30,
    command=self._on_set,
    fg_color=PLANT_COLOR, 
    hover_color=PLANT_HOVER,
    font=ctk.CTkFont(size=11, weight="bold")
)

# Botão Reset
btn_reset = ctk.CTkButton(
    parent, 
    text="🔄 Resetar Ajustes",  # Emoji + texto
    command=self._on_reset,
    fg_color=WARNING_ORANGE, 
    hover_color=STRAW_HOVER,
    font=ctk.CTkFont(size=12, weight="bold")
)
```

### 🎛️ **Controles de Slider**

#### **Estrutura de Slider com Botão**
```python
# Frame para Slider + Botão
control_frame = ctk.CTkFrame(parent, fg_color="transparent")
control_frame.grid(row=1, column=0, sticky="ew", pady=(0, 8), padx=15)
control_frame.columnconfigure(0, weight=1)  # Slider
control_frame.columnconfigure(1, weight=0)  # Botão

# Slider
slider = ctk.CTkSlider(
    control_frame, 
    from_=-5, 
    to=5, 
    number_of_steps=10,
    command=self._on_adjustment,
    progress_color=SLIDER_PLANT, 
    button_color=SLIDER_PLANT_BTN
)
slider.grid(row=0, column=0, sticky="ew", padx=(0, 10))

# Botão SET
btn_set = ctk.CTkButton(
    control_frame, 
    text="SET", 
    width=50, 
    height=30,
    command=self._on_set,
    fg_color=PLANT_COLOR, 
    hover_color=PLANT_HOVER,
    font=ctk.CTkFont(size=11, weight="bold")
)
btn_set.grid(row=0, column=1, sticky="e")
```

### 📊 **Elementos de Display**

#### **Labels de Título**
```python
# Título Principal
title = ctk.CTkLabel(
    panel, 
    text="🎛️ AJUSTES FINOS",  # Emoji + texto em maiúsculo
    font=ctk.CTkFont(size=16, weight="bold"),
    text_color=(TEXT_PRIMARY, "#4a9eff")
)

# Subtítulo
subtitle = ctk.CTkLabel(
    parent, 
    text="🌱 Plantas:",  # Emoji + texto
    font=ctk.CTkFont(size=14, weight="bold")
)
```

#### **Labels de Status**
```python
# Label de Status
status_label = ctk.CTkLabel(
    parent, 
    text="0 - Neutro", 
    font=ctk.CTkFont(size=12), 
    text_color=TEXT_SECONDARY
)

# Label de Percentual
percentage_label = ctk.CTkLabel(
    parent, 
    text=f"Plantas: {value:.1f}%",
    font=ctk.CTkFont(size=12, weight="bold")
)
```

### 📋 **Dropdowns e ComboBoxes**

#### **ComboBox de Visualização**
```python
# ComboBox com callback
view_mode = tk.StringVar(value="overlay")
cmb_view = ctk.CTkComboBox(
    parent, 
    variable=view_mode, 
    values=["original", "mapa", "overlay"], 
    state="readonly", 
    width=160,
    font=ctk.CTkFont(size=12),
    dropdown_font=ctk.CTkFont(size=12),
    command=self._on_view_mode_changed
)
```

### 📈 **Barras de Progresso**

#### **Barra de Progresso**
```python
# Frame da barra
prog_frame = ctk.CTkFrame(parent)
prog_frame.grid(row=1, column=0, sticky="ew")
prog_frame.columnconfigure(0, weight=1)

# Barra de progresso
progress = ctk.CTkProgressBar(prog_frame)
progress.set(0.0)
progress.grid(row=0, column=0, sticky="ew", padx=10, pady=(6, 0))

# Label de status
lbl_progress = ctk.CTkLabel(prog_frame, text="Pronto.")
lbl_progress.grid(row=1, column=0, sticky="w", pady=(4, 0))
```

### 🎨 **Padrões de Espaçamento**

#### **Padding e Margens**
```python
# Padding padrão
PADX_STANDARD = 15
PADY_STANDARD = 15
PADX_SMALL = 5
PADY_SMALL = 5

# Exemplos de uso
widget.grid(row=0, column=0, padx=PADX_STANDARD, pady=PADY_STANDARD)
widget.grid(row=1, column=0, padx=PADX_SMALL, pady=PADY_SMALL)
```

### 🔧 **Padrões de Funcionalidade**

#### **Sistema de Callbacks**
```python
# Padrão de callback para sliders
def _on_adjustment(self, value: float) -> None:
    """Handle adjustment with real-time feedback."""
    adj_value = int(value)
    self._update_label(adj_value)
    
    if self._is_processed:
        result = self.adjuster.set_sensitivity(adj_value)
        if result:
            self._handle_result(result)

# Padrão de callback para botões SET
def _on_set(self) -> None:
    """Handle SET/UNSET toggle."""
    if not self._is_set:
        # SET: Take snapshot
        self._mask_set = self._current_mask.copy()
        self._is_set = True
        self.set_btn.configure(text="UNSET", fg_color=DARKER_COLOR)
    else:
        # UNSET: Clear snapshot
        self._mask_set = None
        self._is_set = False
        self.set_btn.configure(text="SET", fg_color=ORIGINAL_COLOR)
    
    self._update_display()
```

#### **Sistema de Reset**
```python
def _reset_controls(self) -> None:
    """Reset all controls to default state."""
    # Reset sliders
    self.slider1.set(0)
    self.slider2.set(0)
    
    # Reset labels
    self._update_label1(0)
    self._update_label2(0)
    
    # Reset photography system
    self._mask_set = None
    self._is_set = False
    
    # Reset button states
    self.set_btn.configure(text="SET", fg_color=ORIGINAL_COLOR)
```

### 📱 **Responsividade**

#### **Configuração de Grid Responsivo**
```python
# Layout responsivo
def _build_responsive_layout(self):
    # Configuração principal
    self.rowconfigure(0, weight=0)  # Header
    self.rowconfigure(1, weight=1)  # Main content
    self.rowconfigure(2, weight=0)  # Footer
    self.columnconfigure(0, weight=1)
    
    # Área principal com proporção 2:1
    main_content.columnconfigure(0, weight=2)  # Canvas
    main_content.columnconfigure(1, weight=1)  # Panel
```

### 🎯 **Padrões de Nomenclatura**

#### **Convenções de Nomes**
```python
# Variáveis de estado
self._is_processed = False
self._current_mask = None
self._mask_set = None

# Métodos privados
def _on_action(self) -> None:
def _update_display(self) -> None:
def _handle_result(self, result: dict) -> None:

# Métodos de callback
def _on_slider_change(self, value: float) -> None:
def _on_button_click(self) -> None:
def _on_dropdown_change(self, choice=None) -> None:
```

### 🔄 **Sistema de Estados**

#### **Gerenciamento de Estados**
```python
# Estados principais
class AppState:
    IDLE = "idle"
    LOADING = "loading"
    PROCESSING = "processing"
    RESULTS = "results"
    ERROR = "error"

# Transições de estado
def _set_state(self, new_state: str) -> None:
    self._current_state = new_state
    self._update_ui_for_state()

def _update_ui_for_state(self) -> None:
    if self._current_state == AppState.PROCESSING:
        self.btn_process.configure(state="disabled")
        self.progress.start()
    elif self._current_state == AppState.RESULTS:
        self.btn_process.configure(state="normal")
        self.progress.stop()
```

### 📝 **Template de Implementação**

#### **Estrutura Base de Classe**
```python
import tkinter as tk
import customtkinter as ctk
import numpy as np
from typing import Dict, Any, Optional

class YourApp(ctk.CTkFrame):
    def __init__(self, master: tk.Widget) -> None:
        super().__init__(master)
        
        # Estado da aplicação
        self._is_processed = False
        self._current_data = None
        self._mask_set = None
        self._is_set = False
        
        # Inicialização
        self._build_ui()
        self._setup_callbacks()
    
    def _build_ui(self) -> None:
        """Build the user interface."""
        # Configurar grid
        self._setup_grid()
        
        # Construir componentes
        self._build_toolbar()
        self._build_main_area()
        self._build_controls()
        self._build_status()
    
    def _setup_grid(self) -> None:
        """Setup responsive grid layout."""
        # Implementar grid system
        pass
    
    def _build_toolbar(self) -> None:
        """Build top toolbar with action buttons."""
        # Implementar toolbar
        pass
    
    def _build_main_area(self) -> None:
        """Build main content area."""
        # Implementar área principal
        pass
    
    def _build_controls(self) -> None:
        """Build control panels."""
        # Implementar controles
        pass
    
    def _build_status(self) -> None:
        """Build status and progress area."""
        # Implementar status
        pass
```

### 🚀 **Checklist de Implementação**

#### **Elementos Obrigatórios**
- [ ] Paleta de cores consistente
- [ ] Botões com emojis e texto em maiúsculo
- [ ] Sliders com cores temáticas
- [ ] Sistema de grid responsivo
- [ ] Callbacks em tempo real
- [ ] Sistema de estados
- [ ] Barras de progresso
- [ ] Labels de status
- [ ] ComboBoxes com callback
- [ ] Sistema de reset
- [ ] Padding e margens consistentes

#### **Elementos Opcionais**
- [ ] Sistema de fotografia (SET/UNSET)
- [ ] Múltiplas visualizações
- [ ] Exportação de dados
- [ ] Configurações avançadas
- [ ] Temas claro/escuro
- [ ] Animações de transição

### 📋 **Instruções de Uso**

1. **Copie a paleta de cores** para seu projeto
2. **Implemente a estrutura de grid** responsiva
3. **Use os padrões de botões** com emojis e cores
4. **Configure os callbacks** seguindo os exemplos
5. **Implemente o sistema de estados** para controle
6. **Adicione os elementos de UI** seguindo os templates
7. **Teste a responsividade** em diferentes tamanhos
8. **Ajuste as cores** conforme necessário para seu domínio

Este guia fornece todos os elementos necessários para recriar a interface do Easy IOP em qualquer outro software, mantendo a consistência visual e funcional.
