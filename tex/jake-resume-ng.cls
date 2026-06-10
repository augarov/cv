\ProvidesClass{jake-resume-ng}[Jake Resume class]
\NeedsTeXFormat{LaTeX2e}
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{article}}
\ProcessOptions\relax
\LoadClass{article}

\usepackage{latexsym}
\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage{marvosym}
\usepackage[usenames,dvipsnames]{color}
\usepackage{verbatim}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{fancyhdr}
\usepackage[english]{babel}
\usepackage{tabularx}
\usepackage{multicol}
\setlength{\multicolsep}{0pt}
\input{glyphtounicode}

%----------FONT OPTIONS----------
% sans-serif
% \usepackage[sfdefault]{FiraSans}
% \usepackage[sfdefault]{roboto}
% \usepackage[sfdefault]{noto-sans}
% \usepackage[default]{sourcesanspro}

% serif
% \usepackage{CormorantGaramond}
% \usepackage{charter}

\pagestyle{fancy}
\fancyhf{} % clear all header and footer fields
\fancyfoot{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

% Adjust margins
\addtolength{\oddsidemargin}{-0.5in}
\addtolength{\evensidemargin}{-0.5in}
\addtolength{\textwidth}{1in}
\addtolength{\topmargin}{-.5in}
\addtolength{\textheight}{1.0in}

\urlstyle{same}

\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}

%----------------------------------------------------------------------------------------
%   SECTION TITLE FORMATTING AND SPACING
%   Spacing is set explicitly via \titlespacing — no embedded \vspace tricks.
%----------------------------------------------------------------------------------------

\titleformat{\section}{\scshape\raggedright\large}{}{0em}{}[\color{black}\titlerule]
\titlespacing*{\section}{0pt}{0pt}{4pt}

% Named spacing commands (following deedy-resume-ng.cls pattern)
\newcommand{\sectionspace}{\vspace{8pt}} % gap between consecutive section entries

% Ensure that generated pdf is machine readable/ATS parsable
\pdfgentounicode=1

%----------------------------------------------------------------------------------------
%   CUSTOM COMMANDS
%   No ad-hoc \vspace adjustments — all spacing controlled via enumitem list options.
%----------------------------------------------------------------------------------------

\newcommand{\resumeItem}[1]{\item\small{#1}}

\newcommand{\resumeSubheading}[4]{
  \item
    \begin{tabular*}{0.97\textwidth}[t]{l@{\extracolsep{\fill}}r}
      \textbf{#1} & #2 \\
      \textit{\small#3} & \textit{\small #4} \\
    \end{tabular*}
}

\newcommand{\resumeSubSubheading}[2]{
  \item
    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
      \textit{\small#1} & \textit{\small #2} \\
    \end{tabular*}
}

\newcommand{\resumeProjectHeading}[2]{
  \item
    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
      #1 & #2 \\
    \end{tabular*}
}

\newcommand{\resumeSubItem}[1]{\resumeItem{#1}}

\newcommand{\resumebullet}{$\vcenter{\hbox{\tiny$\bullet$}}$}

\newcommand{\resumeSkillCategoryHeading}[1]{\item\textbf{#1}}

\newcommand{\resumeMulticolItemListStart}[1]{%
  \begin{multicols}{#1}
  \begin{itemize}[topsep=0pt, itemsep=0pt, parsep=0pt, partopsep=0pt, label=\resumebullet]}
\newcommand{\resumeMulticolItemListEnd}{\end{itemize}\end{multicols}}

\newcommand{\resumeSubsectionText}[1]{\noindent{\small #1}}

%----------------------------------------------------------------------------------------
%   LIST ENVIRONMENTS
%   All spacing set via enumitem options — consistent regardless of what content
%   follows a subheading (description, bullets, or technology stack).
%----------------------------------------------------------------------------------------

% Outer list: top-level section entries (jobs, education items, projects).
% itemsep controls the vertical gap between consecutive entries.
\newcommand{\resumeSubHeadingListStart}{%
  \begin{itemize}[leftmargin=0.15in, label={},
    topsep=0pt, itemsep=6pt, parsep=0pt, partopsep=0pt]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}

% Inner list: achievement bullets within a section entry.
% topsep provides a small gap after the preceding subheading or description text.
\newcommand{\resumeItemListStart}{%
  \begin{itemize}[topsep=0pt, itemsep=0pt, parsep=0pt, partopsep=0pt, label=\resumebullet]}
\newcommand{\resumeItemListEnd}{\end{itemize}}
