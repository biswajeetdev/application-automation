# Application Automation

![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-2EAD33?style=flat&logo=playwright&logoColor=white)
![YAML](https://img.shields.io/badge/YAML-CB171E?style=flat&logo=yaml&logoColor=white)

Playwright-based CLI that fills job application forms automatically — review before submitting.

Currently supports **Greenhouse ATS** (used by Rubrik, Stripe, Notion, and 10,000+ companies).

## Quickstart

```bash
pip install -r requirements.txt
playwright install chromium

cp profile.example.yaml profile.yaml   # fill in your details
python apply.py --url <greenhouse-job-url> --profile profile.yaml
# ^ fills the form and saves a screenshot — does NOT submit

python apply.py --url <greenhouse-job-url> --profile profile.yaml --submit
# ^ submits after you've verified the screenshot
```

## Profile format

See `profile.example.yaml`. Your `profile.yaml` is gitignored — never commit it.

## How it works

1. Navigates to the job URL in a real Chromium browser (visible, not headless)
2. Fills all standard fields: name, email, phone, location, LinkedIn
3. Uploads resume PDF and injects cover letter text
4. Handles work-authorization dropdowns via label matching
5. Takes a full-page screenshot for review
6. Only submits when `--submit` is explicitly passed

## Design decisions

- **Headed browser by default** — you can watch it fill in real time and catch issues
- **Screenshot before submit** — mandatory review step, not optional
- **YAML profile** — separates your personal data from the automation code
- **Label-based custom question matching** — works across different Greenhouse form configurations without hardcoded selectors

## Roadmap

- [ ] Lever ATS support
- [ ] Ashby ATS support
- [ ] Multi-URL batch mode (apply to many jobs from a CSV)
- [ ] Session persistence (resume interrupted runs)
