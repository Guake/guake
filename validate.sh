#!/bin/bash

if [[ ! -z $1 ]] && [[ $1 == "--help" ]]; then
    echo "USAGE: validate.sh [oldrev [--quick]]"
    echo "  This script will test a set of patches (oldrev..HEAD) for basic acceptability as a patch"
    echo "  Run it in an activated virtualenv with the current Buildbot installed, as well as"
    echo "      sphinx, pyflakes, mock, and so on"
    echo "To use a different directory for tests, pass TRIALTMP=/path as an env variable"
    echo "if --quick is passed validate will skip unit tests and concentrate on coding style"
    echo
    echo "If no argument is given, all files from current directory will be inspected"
    exit 1
fi

REVRANGE=
if [ ! -z $1 ]; then
    REVRANGE="$1..HEAD"
fi
TRIAL_TESTS=

# some colors
# plain
_ESC=$'\e'
GREEN="$_ESC[0;32m"
MAGENTA="$_ESC[0;35m"
RED="$_ESC[0;31m"
LTCYAN="$_ESC[1;36m"
YELLOW="$_ESC[1;33m"
NORM="$_ESC[0;0m"


function status()
{
    echo "${LTCYAN}-- ${*} --${NORM}"
}

slow=true
if [[ $2 == '--quick' ]]; then
    slow=false
fi
ok=true
problem_summary=""

function not_ok()
{
    ok=false
    echo "${RED}** ${*} **${NORM}"
    problem_summary="$problem_summary"$'\n'"${RED}**${NORM} ${*}"
}

function warning()
{
    echo "${YELLOW}** ${*} **${NORM}"
    problem_summary="$problem_summary"$'\n'"${YELLOW}**${NORM} ${*} (warning)"
}

function check_tabs()
{
    git diff "$REVRANGE" | grep -q $'+.*\t'
}

function check_relnotes()
{
    if git diff --exit-code "$REVRANGE" master/docs/relnotes/index.rst >/dev/null 2>&1; then
        return 1
    else
        return 0
    fi
}

function run_tests()
{
    if [ -z $TRIAL_TESTS ]; then
        return
    fi
    if [ -n "${TRIALTMP}" ]; then
        TEMP_DIRECTORY_OPT="--temp-directory ${TRIALTMP}"
    fi
    find . -name \*.pyc -exec rm {} \;
    trial --reporter text ${TEMP_DIRECTORY_OPT} ${TRIAL_TESTS}
}

if [ -z $REVRANGE ]; then
    py_files=$(find . -name "*.py" -o -name "*.py.in" | grep -v -E 'src/guake/globals.py$' | grep -v -E 'doc/src/conf.py$')
    echo "Validating files: "
    echo $py_files
else

    if ! git diff --no-ext-diff --quiet --exit-code; then
        not_ok "changed files in working copy"
        if $slow; then
            exit 1
        fi
    fi
    # get a list of changed files, used below; this uses a tempfile to work around
    # shell behavior when piping to 'while'
    tempfile=$(mktemp)
    trap 'rm -f ${tempfile}' 1 2 3 15
    git diff --name-only $REVRANGE | grep -E '(src/guake\/guake$|\.py$)' | grep -v '\(^master/\(contrib\|docs\)\|/setup\.py\)' > ${tempfile}
    py_files=()
    while read line; do
        if test -f "${line}"; then
            py_files+=($line)
        fi
    done < ${tempfile}

    echo "${MAGENTA}Validating the following commits:${NORM}"
    git --no-pager log "$REVRANGE" --pretty=oneline || exit 1

    if $slow; then
        status "running tests"
        run_tests || not_ok "tests failed"
    fi

    status "checking formatting"
    check_tabs && not_ok "$REVRANGE adds tabs"

    status "checking for release notes"
    check_relnotes || warning "$REVRANGE does not add release notes"
fi

status "checking import module convention in modified files"
RES=true
for filename in ${py_files[@]}; do
  if ! python2.7 fiximports.py "$filename"; then
    echo "cannot fix imports of $filename"
    RES=false
  fi
done
$RES || warning "some import fixes failed -- not enforcing for now"

status "running autopep8"
if [[ -z `which autopep8` ]]; then
    warning "autopep8 is not installed"
elif [[ ! -f pep8rc ]]; then
    warning "pep8rc not found"
else
    changes_made=false
    for filename in ${py_files[@]}; do
        LINEWIDTH=$(grep -E "max-line-length" pep8rc | sed 's/ //g' | cut -d'=' -f 2)
        # even if we dont enforce errors, if they can be fixed automatically, thats better..
        IGNORES=W6
        # ignore is not None for SQLAlchemy code..
        if [[ "$filename" =~ "/db/" ]]; then
            IGNORES=$IGNORES,E711,E712
        fi
        autopep8 --in-place --max-line-length=$LINEWIDTH --ignore=$IGNORES "$filename"
        if ! git diff --quiet --exit-code "$filename"; then
            changes_made=true
        fi
    done
    if ${changes_made}; then
        not_ok "autopep8 made changes"
    fi
fi

status "running pep8"
if [[ -z `which pep8` ]]; then
    warning "pep8 is not installed"
elif [[ ! -f pep8rc ]]; then
    warning "pep8rc not found"
else
    pep8_ok=true
    for filename in ${py_files[@]}; do
        if ! pep8 --config=pep8rc "$filename"; then
            pep8_ok=false
        fi
    done
    $pep8_ok || not_ok "pep8 failed"
fi

status "running pyflakes"
if [[ -z `which pyflakes` ]]; then
    warning "pyflakes is not installed"
else
    pyflakes_ok=true
    for filename in ${py_files[@]}; do
        if ! pyflakes "$filename"; then
            pyflakes_ok=false
        fi
    done
    $pyflakes_ok || not_ok "pyflakes failed"
fi


status "running pylint"
if [[ -z `which pylint` ]]; then
    warning "pylint is not installed"
elif [[ ! -f pylintrc ]]; then
    warning "pylintrc not found"
else
    pylint_ok=true
    for filename in ${py_files[@]}; do
        if ! pylint --rcfile=pylintrc --disable=R,line-too-long --enable=W0611 --output-format=text --report=no "$filename"; then
            pylint_ok=false
        fi
    done
    $pylint_ok || not_ok "pylint failed"
fi

echo ""
if $ok; then
    if [ -z "${problem_summary}" ]; then
        echo "${GREEN}GOOD!${NORM}"
    else
        echo "${YELLOW}WARNINGS${NORM}${problem_summary}"
    fi
    exit 0
else
    echo "${RED}NO GOOD!${NORM}${problem_summary}"
    exit 1
fi
