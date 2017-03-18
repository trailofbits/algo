## Table of Contents

1. [Error: "You have not agreed to the Xcode license agreements"](#1-error-you-have-not-agreed-to-the-xcode-license-agreements)
2. [Error: "fatal error: 'openssl/opensslv.h' file not found"](#2-error-fatal-error-opensslopensslvh-file-not-found)
3. [Little Snitch is broken when connected to the VPN](#3-little-snitch-is-broken-when-connected-to-the-vpn)
4. [Various websites appear to be offline through the VPN](#4-various-websites-appear-to-be-offline-through-the-vpn)
5. 
6. [I have a problem not covered here](i-have-a-problem-not-covered-here)

### 1. Error: "You have not agreed to the Xcode license agreements"

On macOS, did you try to install the dependencies with pip and encounter the following error?

```
Downloading cffi-1.9.1.tar.gz (407kB): 407kB downloaded
  Running setup.py (path:/private/tmp/pip_build_root/cffi/setup.py) egg_info for package cffi

You have not agreed to the Xcode license agreements, please run 'xcodebuild -license' (for user-level acceptance) or 'sudo xcodebuild -license' (for system-wide acceptance) from within a Terminal window to review and agree to the Xcode license agreements.

    No working compiler found, or bogus compiler options
    passed to the compiler from Python's distutils module.
    See the error messages above.
    (If they are about -mno-fused-madd and you are on OS/X 10.8,
    see http://stackoverflow.com/questions/22313407/ .)

----------------------------------------
Cleaning up...
Command python setup.py egg_info failed with error code 1 in /private/tmp/pip_build_root/cffi
Storing debug log for failure in /Users/algore/Library/Logs/pip.log
```

The Xcode compiler is installed but requires you to accept its license agreement prior to using it. Run `xcodebuild -license` to agree and then retry installing the dependencies.

### 2. Error: "fatal error: 'openssl/opensslv.h' file not found"

On macOS, did you try to install pycrypto and encounter the following error?

```
build/temp.macosx-10.12-intel-2.7/_openssl.c:434:10: fatal error: 'openssl/opensslv.h' file not found

#include <openssl/opensslv.h>

        ^

1 error generated.

error: command 'cc' failed with exit status 1

----------------------------------------
Cleaning up...
Command /usr/bin/python -c "import setuptools, tokenize;__file__='/private/tmp/pip_build_root/cryptography/setup.py';exec(compile(getattr(tokenize, 'open', open)(__file__).read().replace('\r\n', '\n'), __file__, 'exec'))" install --record /tmp/pip-sREEE5-record/install-record.txt --single-version-externally-managed --compile failed with error code 1 in /private/tmp/pip_build_root/cryptography
Storing debug log for failure in /Users/algore/Library/Logs/pip.log
```

You are running an old version of `pip` that cannot build the `pycrypto` dependency. Upgrade to a new version of `pip` by running `sudo pip install -U pip`.

### 3. Little Snitch is broken when connected to the VPN

Little Snitch is not compatible with IPSEC VPNs due to a known bug in macOS and there is no solution. The Little Snitch "filter" does not get incoming packets from IPSEC VPNs and, therefore, cannot evaluate any rules over them. Their developers have filed a bug report with Apple but there has been no response. There is nothing they or Algo can do to resolve this problem on their own. You can read more about this problem in [issue #134](https://github.com/trailofbits/algo/issues/134).

### 4. Various websites appear to be offline through the VPN

This issue appears intermittently due to issues with MTU size. If you experience this issue, we recommend [filing an issue](https://github.com/trailofbits/algo/issues/new) for assistance. Advanced users can troubleshoot the correct MTU size by retrying `ping` with the "don't fragment" bit size and decreasing packet size. This will determine the correct MTU size for your network, which you then need to update on your network adapter.

### 5. Bad owner or permissions on .ssh

You tried to run Algo and it quickly exits with an error about a bad owner or permissions:

```
fatal: [104.236.2.94]: UNREACHABLE! => {"changed": false, "msg": "Failed to connect to the host via ssh: Bad owner or permissions on /home/user/.ssh/config\r\n", "unreachable": true}
```

You need to reset the permissions on your `.ssh` directory. Run `chmod 700 /home/user/.ssh` and then `chmod 600 /home/user/.ssh/config`. You may need to repeat this for other files mentioned in the error message.

### I have a problem not covered here

If you have an issue that you cannot solve with the guidance here, [join our Slack](https://empireslacking.herokuapp.com/) and ask for help in the #tool-algo channel or [file an issue](https://github.com/trailofbits/algo/issues/new) that describes the problem and we'll do our best to help you.

