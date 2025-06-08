%----------------------------------------------------------------------------------------
%	CLASS OPTIONS AND REQUIRED PACKAGES
%----------------------------------------------------------------------------------------

\ProvidesClass{deedy-resume}[2014/04/30 CV class]
\NeedsTeXFormat{LaTeX2e}
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{article}}
\ProcessOptions\relax
\LoadClass{article}

\usepackage[hidelinks]{hyperref} % Hidden links
\usepackage{supertabular} % Required for the supertabular environment which allows tables to span multiple pages so sections with tables correctly wrap across pages
\usepackage{enumitem} % For compact itemize
\usepackage{accsupp} % Allows copying text from PDF

%----------------------------------------------------------------------------------------
%	MARGINS
%----------------------------------------------------------------------------------------

\usepackage[
	a4paper, % Paper size
	top=0.75cm, % Top margin
	bottom=0.75cm, % Bottom margin
	left=1.25cm, % Left margin
	right=1.25cm, % Right margin
	footskip=1cm, % Space from the bottom margin to the baseline of the footer
	headsep=0.5cm, % Space from the top margin to the baseline of the header
	headheight=1cm, % Height of the header
	% showframe % Uncomment to show frames around the margins for debugging purposes
]{geometry}

%----------------------------------------------------------------------------------------
%	COLORS
%----------------------------------------------------------------------------------------

\usepackage[dvipsnames]{xcolor} % Required for custom colors

\definecolor{primary}{HTML}{2b2b2b} % The primary document color for content text
\definecolor{headings}{HTML}{6A6A6A} % The color of the large sections
\definecolor{subheadings}{HTML}{333333} % The color of subsections and places worked/studied
\definecolor{date}{HTML}{666666} % The color used for the Last Updated text at the top right
\definecolor{shade}{HTML}{F0F0F0} % The color for the contact information box

%----------------------------------------------------------------------------------------
%	FONTS
%----------------------------------------------------------------------------------------

\usepackage{fontspec} % Required for specifying custom fonts in XeLaTeX
\usepackage{fontawesome5} % Font with icons
\usepackage{pifont} % More styles for bullets

% The primary font for content text; defines bold, italic and bold-italic as well
\setmainfont[
	Color=primary,
	Path = fonts/lato/,
	Extension=.ttf,
	UprightFont=Lato-Lig,
	ItalicFont=Lato-LigIta,
	BoldFont=Lato-Reg,
	BoldItalicFont=Lato-RegIta,
]{Lato-Lig}

% The font used where \sfffamily is called
\setsansfont[
	Scale=MatchLowercase,
	Mapping=tex-text,
	Path = fonts/raleway/
]{Raleway-ExtraLight}

%----------------------------------------------------------------------------------------
%	LAST UPDATED COMMAND
%----------------------------------------------------------------------------------------

\usepackage[absolute]{textpos} % Required for positioning the Last Updated text at the top right of the page
\usepackage[UKenglish]{isodate} % Prints the Last Updated date in UK English format

\setlength{\TPHorizModule}{0.01\paperwidth} % Sets the units for the horizontal position used in the \begin{textblock} argument
\setlength{\TPVertModule}{0.01\paperwidth} % Sets the units for the vertical position used in the \begin{textblock} argument
\newcommand{\lastupdated}{ % Create a new command for printing the Last Updated text
\begin{textblock}{28}(70,2) % The position of the Last Updated text on the page
\color{date}\fontspec[Path = fonts/raleway/]{Raleway-ExtraLight}\fontsize{8pt}{10pt}\selectfont % Text styling of the text
\hfill Last Updated on \today % Last Updated text
\end{textblock}}

%----------------------------------------------------------------------------------------
%	MAIN HEADING COMMAND
%----------------------------------------------------------------------------------------

\newcommand{\namesection}[3]{ % Defines the command for the main heading
    \fontsize{40pt}{60pt} % Font size
    \fontspec[Path = fonts/lato/]{Lato-Hai}\selectfont #1 % First name font
    \fontspec[Path = fonts/lato/]{Lato-Lig}\selectfont #2 % Last name font
    \sectionspace\\
    \color{headings}\raggedright\fontspec[Path = fonts/lato/]{Lato-Reg}\fontsize{11pt}{14pt}\selectfont #3
}

%----------------------------------------------------------------------------------------
%	SECTION TITLE STYLING AND SPACING
%----------------------------------------------------------------------------------------

\usepackage{titlesec} % Required for customizing section/subsection/etc titles

\titlespacing{\section}{0pt}{0pt}{0pt} % Removes the spacing around the main section titles
\titlespacing{\subsection}{0pt}{0pt}{0pt} % Removes the spacing around the subsections
\newcommand{\halfspace}{\vspace{4pt}} % Add a set amount of space after sections and subsections
\newcommand{\sectionspace}{\vspace{8pt}} % Add a set amount of space after sections and subsections
\newcommand{\blockspace}{\vspace{12pt}} % Add a set amount of space after big blocks
\newcommand{\columnspace}{\hspace{14pt}} % Add a set amount of space between vertical columns

\titleformat{\section}{ % Customize the large section titles
\color{headings}\fontspec[Path = fonts/lato/]{Lato-Lig}\fontsize{16pt}{24pt}\selectfont \raggedright\uppercase}{}{0em}{}

\newcommand{\runsubsection}[1]{ % Used for creating subsections where a description is required on the same line
\color{subheadings}\fontspec[Path = fonts/lato/]{Lato-Bol}\fontsize{12pt}{12pt}\selectfont\uppercase {#1} \normalfont}

\newcommand{\descript}[1]{ % Used for describing the subsection either on the same line or underneath
\color{subheadings}\raggedright\fontspec[Path = fonts/raleway/]{Raleway-Medium}\fontsize{11pt}{13pt}\selectfont\scshape {#1 \\} \normalfont}

\newcommand{\location}[1]{ % Used for specifying a duration and/or location under a subsection
\color{headings}\raggedright\fontspec[Path = fonts/raleway/]{Raleway-Medium}\fontsize{10pt}{12pt}\selectfont {#1\\} \normalfont}

%----------------------------------------------------------------------------------------
%	LISTS STYLING AND SPACING
%----------------------------------------------------------------------------------------


\newenvironment{descritemize} % Defines the descritemize environment for the Experience Description section
{\begin{itemize}[noitemsep,topsep=0pt,parsep=0pt,partopsep=0pt,rightmargin=0pt,leftmargin=24pt]}
{\end{itemize}}

\newcommand{\descritem}{\item[\BeginAccSupp{ActualText=*}\ding{226}\EndAccSupp{}]} % Arrow-style bullets for the Experience Description section

\newenvironment{skillitemize} % Defines the skillitemize environment for the Skills section
{\begin{itemize}[noitemsep,topsep=0pt,parsep=0pt,partopsep=0pt,rightmargin=0pt,leftmargin=16pt]}
{\end{itemize}}

\newcommand{\skillitem}{\item[\BeginAccSupp{ActualText=*}\labelitemi\EndAccSupp{}]} % Bullets for the Skills section