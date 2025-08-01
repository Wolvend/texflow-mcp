#!/usr/bin/env python3
"""LaTeX templates and utilities for long-form content"""

TEMPLATES = {
    "book": {
        "main.tex": r"""\documentclass[12pt,oneside]{book}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{amsmath,amssymb,amsthm}
\usepackage{graphicx}
\usepackage{hyperref}
\usepackage[margin=1in]{geometry}
\usepackage{setspace}
\onehalfspacing

% For long documents
\usepackage{microtype} % Better typography
\usepackage{lipsum} % For dummy text
\usepackage{tocbibind} % Add bibliography to TOC

\title{Your Book Title}
\author{Your Name}
\date{\today}

\begin{document}

\frontmatter
\maketitle
\tableofcontents
\listoffigures
\listoftables

\mainmatter
\input{chapters/introduction}
\input{chapters/chapter1}
\input{chapters/chapter2}
% Add more chapters as needed

\backmatter
\bibliographystyle{plain}
\bibliography{references}

\end{document}
""",
        "chapters/introduction.tex": r"""\chapter{Introduction}

This is the introduction to your book.

\section{Overview}
% Your content here

\section{Structure}
This book is organized as follows:
""",
        "chapters/chapter1.tex": r"""\chapter{First Chapter}

\section{Introduction}
% Chapter content

\section{Main Content}
% Your writing here

\section{Conclusion}
% Chapter summary
""",
    },
    
    "thesis": {
        "main.tex": r"""\documentclass[12pt,oneside]{report}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{amsmath,amssymb,amsthm}
\usepackage{graphicx}
\usepackage{hyperref}
\usepackage[margin=1.5in]{geometry}
\usepackage{setspace}
\doublespacing

% Theorem environments
\newtheorem{theorem}{Theorem}[chapter]
\newtheorem{lemma}[theorem]{Lemma}
\newtheorem{proposition}[theorem]{Proposition}
\newtheorem{corollary}[theorem]{Corollary}
\theoremstyle{definition}
\newtheorem{definition}[theorem]{Definition}
\newtheorem{example}[theorem]{Example}

\title{Your Thesis Title}
\author{Your Name}
\date{\today}

\begin{document}

\maketitle

\begin{abstract}
Your abstract here...
\end{abstract}

\tableofcontents
\listoffigures
\listoftables

\input{chapters/introduction}
\input{chapters/literature_review}
\input{chapters/methodology}
\input{chapters/results}
\input{chapters/discussion}
\input{chapters/conclusion}

\bibliographystyle{plain}
\bibliography{references}

\appendix
\input{appendices/appendix_a}

\end{document}
""",
    },
    
    "math-heavy": {
        "main.tex": r"""\documentclass[11pt]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{amsmath,amssymb,amsthm,mathtools}
\usepackage{physics} % For derivatives, vectors, etc.
\usepackage{tikz} % For diagrams
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}
\usepackage{hyperref}
\usepackage[margin=1in]{geometry}

% Custom commands for common operations
\newcommand{\R}{\mathbb{R}}
\newcommand{\N}{\mathbb{N}}
\newcommand{\Z}{\mathbb{Z}}
\newcommand{\Q}{\mathbb{Q}}
\newcommand{\C}{\mathbb{C}}
\DeclareMathOperator*{\argmax}{arg\,max}
\DeclareMathOperator*{\argmin}{arg\,min}

% Theorem environments
\newtheorem{theorem}{Theorem}
\newtheorem{lemma}[theorem]{Lemma}
\newtheorem{proposition}[theorem]{Proposition}
\newtheorem{corollary}[theorem]{Corollary}
\theoremstyle{definition}
\newtheorem{definition}[theorem]{Definition}
\newtheorem{example}[theorem]{Example}
\theoremstyle{remark}
\newtheorem*{remark}{Remark}
\newtheorem*{note}{Note}

\title{Mathematical Document}
\author{Your Name}
\date{\today}

\begin{document}

\maketitle

\begin{abstract}
This document contains extensive mathematical content.
\end{abstract}

\section{Introduction}

\section{Mathematical Foundations}

\begin{definition}[Example Definition]
Let $X$ be a topological space. We say that $X$ is \emph{compact} if every open cover has a finite subcover.
\end{definition}

\begin{theorem}[Example Theorem]
Let $f: \R \to \R$ be continuous. Then $f$ is uniformly continuous on any compact subset $K \subseteq \R$.
\end{theorem}

\begin{proof}
% Your proof here
\end{proof}

\section{Complex Equations}

Consider the following system of differential equations:
\begin{align}
    \frac{\partial u}{\partial t} &= \nabla^2 u + f(u,v) \\
    \frac{\partial v}{\partial t} &= D\nabla^2 v + g(u,v)
\end{align}

\end{document}
""",
    },
    
    "novel": {
        "main.tex": r"""\documentclass[12pt,oneside]{book}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[margin=1in]{geometry}
\usepackage{setspace}
\onehalfspacing
\usepackage{indentfirst}
\usepackage{microtype}

% Novel-specific formatting
\usepackage{fancyhdr}
\pagestyle{fancy}
\fancyhf{}
\fancyhead[C]{\textit{\leftmark}}
\fancyfoot[C]{\thepage}
\renewcommand{\chaptermark}[1]{\markboth{#1}{}}

% Remove chapter numbers
\usepackage{titlesec}
\titleformat{\chapter}[display]
  {\normalfont\huge\bfseries\centering}
  {}
  {0pt}
  {\Huge}
\titlespacing*{\chapter}{0pt}{50pt}{40pt}

\title{Your Novel Title}
\author{Your Name}
\date{}

\begin{document}

\frontmatter
\maketitle

\mainmatter
\input{chapters/chapter01}
\input{chapters/chapter02}
\input{chapters/chapter03}
% Continue adding chapters

\backmatter
% Acknowledgments, author bio, etc.

\end{document}
""",
        "chapters/chapter01.tex": r"""\chapter{Chapter One}

The opening of your story begins here. LaTeX will handle the formatting, letting you focus on the narrative.

``Dialogue looks like this,'' she said.

New paragraphs are created with blank lines, maintaining consistent indentation throughout your novel.

% Scene break
\begin{center}
* * *
\end{center}

The next scene begins here...
""",
    }
}

# Utilities for handling long content
MATH_SNIPPETS = {
    "matrix": r"\begin{pmatrix} a & b \\ c & d \end{pmatrix}",
    "integral": r"\int_{-\infty}^{\infty} f(x) \, dx",
    "sum": r"\sum_{n=1}^{\infty} \frac{1}{n^2}",
    "limit": r"\lim_{x \to \infty} f(x)",
    "partial": r"\frac{\partial f}{\partial x}",
    "nabla": r"\nabla \cdot \mathbf{F}",
    "tensor": r"T^{\mu\nu} = \frac{\partial \mathcal{L}}{\partial (\partial_\mu \phi)} \partial^\nu \phi - g^{\mu\nu} \mathcal{L}",
}

def get_template(template_name: str) -> dict:
    """Get a project template"""
    return TEMPLATES.get(template_name, TEMPLATES["article"])

def create_book_chapter(number: int, title: str) -> str:
    """Create a new book chapter template"""
    return f"""\\chapter{{{title}}}

\\section{{Introduction}}
% Introduce the chapter's themes and objectives

\\section{{Main Content}}
% The primary content of your chapter

\\section{{Key Points}}
% Summarize important takeaways

\\section{{Conclusion}}
% Wrap up the chapter and transition to the next
"""

def create_math_environment(env_type: str, label: str, content: str) -> str:
    """Create a mathematical environment"""
    environments = {
        "theorem": "theorem",
        "lemma": "lemma",
        "proof": "proof",
        "definition": "definition",
        "example": "example",
    }
    
    env = environments.get(env_type, "theorem")
    
    if env == "proof":
        return f"\\begin{{proof}}\n{content}\n\\end{{proof}}"
    else:
        return f"\\begin{{{env}}}[{label}]\n{content}\n\\end{{{env}}}"