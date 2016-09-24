#!/bin/bash
# vim: set ts=4 sts=4 sw=4 noet:

# This is a quick script that notifies buildbot of changes
# to a CVS repository. It should be run from the CVS loginfo
# hook, like so:
#
# admit /chara/carmaweb/buildbot/cvs-update.bash %{sVv}

# Parse apart the arguments, which look like this:
# cvs/module filename,oldrev,newrev

# return 0 if host is alive in $?
# isHostAlive hostname
function isHostAlive() {
	ping -c 2 -q $1 > /dev/null 2>&1
	return $?
}

CATEGORY="$(echo "$1" | awk -F' ' '{ print $1; }')"
FILEREV="$(echo "$1" | awk -F' ' '{ print $2; }')"

CHANGED="$(echo "$FILEREV" | awk -F',' '{ print $1 ; }')"
OLDREV="$(echo "$FILEREV" | awk -F',' '{ print $2 ; }')"
NEWREV="$(echo "$FILEREV" | awk -F',' '{ print $3 ; }')"

COMMITTER=$2

# NOTE: do not use the file revision, let buildbot
# NOTE: use the date automatically instead. Without
# NOTE: atomic commits like svn, it doesn't work

#MASTER_SERVER="asako.correlator.pvt"
#MASTER_SERVER="harkless.ovro.pvt"
MASTER_SERVER="chara.astro.umd.edu"
CVS_SERVER="chara.astro.umd.edu"

# check that this is only run on dana
if [[ "$(hostname)" != "$CVS_SERVER" ]]; then
	echo "NOTICE: Your CVS repository is being accessed over NFS, rather than SSH."
	echo "NOTICE: Therefore, CVS is unable to notify buildbot about this change."
	echo "NOTICE: Switch your repository access to SSH to make this message go away."
	echo
	echo "NOTICE: This is not an error, and is not fatal!"

	# exit cleanly
	exit 0
fi

# check for connectivity
if isHostAlive $MASTER_SERVER ; then

	source /chara/carmaweb/buildbot/sandboxes/$HOSTNAME/bin/activate
	buildbot sendchange --master $MASTER_SERVER:9989 \
			    --who $COMMITTER --logfile - \
			    --category "$CATEGORY" \
			    --revision "$(date)" \
				--vc cvs \
			    "$CHANGED" &>/dev/null
else
	echo "$MASTER_SERVER could not be reached. Buildbot not updated"
fi

exit 0

