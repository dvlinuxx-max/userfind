# userfind

Check whether a username exists across a set of public platforms. Given a
handle, userfind requests each site's public profile URL and reports where an
account with that name appears to exist. It reads only publicly available pages.

## Responsible use

This is an OSINT tool for research and investigations you are authorized to
perform. Do not use it to stalk, harass, or de-anonymize anyone. A username
matching on two sites does not mean the same person owns both — handles collide.
Treat results as leads, not facts.

## Usage

```bash
python userfind.py torvalds
python userfind.py torvalds --all      # also show absent/blocked
python userfind.py torvalds --json
```

## Example

```
$ python userfind.py torvalds

userfind torvalds  6 of 12 sites

  + GitHub       https://github.com/torvalds
  + GitLab       https://gitlab.com/torvalds
  + Keybase      https://keybase.io/torvalds
  + Medium       https://medium.com/@torvalds
  ...
```

## How it works

```
userfind.py
  SITES    profile URL template + detection mode per site
  check    request the URL; decide found/absent/blocked
  main     run all checks concurrently (ThreadPoolExecutor)
```

Detection is either by HTTP status (`404` means absent) or by a marker string
that only appears on a site's "not found" page. Sites behind anti-bot
protection return `blocked`/`unknown` rather than a false answer — the tool is
honest about what it could not determine.

## Requirements

Python 3.9+, network access. No third-party packages.

## License

MIT
