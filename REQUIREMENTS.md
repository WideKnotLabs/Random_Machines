# RMXY-1 Public Site Requirements

## Identity

- Company/brand name: Random Machines
- App name: RMXY-1
- Apple developer/publisher name: Borja Deudero Gracia
- Support and privacy contact: `wideknotlabs@gmail.com`

## App Store URLs

Use these final URL paths when the domain is ready:

- Marketing URL: `https://your-domain.com/rmxy-1/`
- Support URL: `https://your-domain.com/rmxy-1/support/`
- Privacy Policy URL: `https://your-domain.com/rmxy-1/privacy/`
- CMake `COMPANY_WEBSITE`: `https://your-domain.com/rmxy-1/`

## Common Rules

- Public pages only: no login, password, or account gate.
- HTTPS only when published.
- Mobile-friendly layout.
- No "coming soon" or placeholder user-facing copy.
- No broken contact links.
- Same identity across all pages: RMXY-1, Random Machines, Borja Deudero Gracia.
- No analytics, tracking pixels, newsletter forms, advertising scripts, or cloud media upload claims while the privacy policy says no data is collected.
- Footer links to Support and Privacy Policy on every page.

## Page Purposes

- `/rmxy-1/`: marketing page explaining what RMXY-1 is.
- `/rmxy-1/support/`: support page with contact information and common issues.
- `/rmxy-1/privacy/`: privacy policy for App Store Connect.

## Before Publishing

- Replace `https://your-domain.com` with the real domain if using a custom domain.
- Confirm the App Store Connect privacy answers match the policy. With no analytics, crash telemetry, accounts, cloud sync, or tracking SDKs, the likely answer is "No, we do not collect data from this app."
- Add real app screenshots to the marketing page when available. Do not add screenshot placeholders.
- Add any legally required EU trader/contact details to the support page if they apply.

## App Store Wording

Use this wording for public App Store privacy/support descriptions:

RMXY-1 uses microphone input in the standalone app for live audio processing. Audio is processed locally on device and is not uploaded, stored on our servers, or shared. The AUv3 extension processes audio provided by the host app.

The standalone app does not currently provide background audio. When RMXY-1 is used as an AUv3 extension, audio behavior is controlled by the host app.

## App Review Notes

RMXY-1 uses microphone input in the standalone app for local live audio processing. The AUv3 extension receives audio from the host app and does not request microphone access directly. RMXY-1 does not upload, collect, or share audio.
