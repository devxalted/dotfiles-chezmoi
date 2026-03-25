// Enable userChrome.css
user_pref("toolkit.legacyUserProfileCustomizations.stylesheets", true);

// Minimal UI
user_pref("browser.uidensity", 1); // compact mode
user_pref("browser.compactmode.show", true);
user_pref("browser.tabs.inTitlebar", 0); // no titlebar integration

// Disable annoying features
user_pref("browser.aboutConfig.showWarning", false);
user_pref("browser.shell.checkDefaultBrowser", false);
user_pref("browser.newtabpage.enabled", false);
user_pref("browser.startup.homepage_override.mstone", "ignore");
user_pref("browser.translations.automaticallyPopup", false);

// Blank new tab
user_pref("browser.newtabpage.activity-stream.feeds.section.topstories", false);
user_pref("browser.newtabpage.activity-stream.feeds.topsites", false);
user_pref("browser.newtabpage.activity-stream.showSponsored", false);
user_pref("browser.newtabpage.activity-stream.showSponsoredTopSites", false);

// Dark theme
user_pref("extensions.activeThemeID", "firefox-compact-dark@mozilla.org");
user_pref("ui.systemUsesDarkTheme", 1);

// Smooth scrolling
user_pref("general.smoothScroll", true);

// Dev tools dark theme
user_pref("devtools.theme", "dark");
