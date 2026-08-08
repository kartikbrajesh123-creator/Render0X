const themes = {
    purple: {
        primary: "#d52cff",
        secondary: "#318cff"
    },

    blue: {
        primary: "#00b7ff",
        secondary: "#3867ff"
    },

    green: {
        primary: "#00e676",
        secondary: "#00bfa5"
    },

    red: {
        primary: "#ff315c",
        secondary: "#ff1744"
    },

    orange: {
        primary: "#ff8a00",
        secondary: "#ff3d00"
    },

    pink: {
        primary: "#ff4fcf",
        secondary: "#9c4dff"
    }
};


function applyRender0XTheme(themeName) {

    const theme = themes[themeName];

    if (!theme) return;

    document.documentElement.style.setProperty(
        "--primary",
        theme.primary
    );

    document.documentElement.style.setProperty(
        "--secondary",
        theme.secondary
    );

    localStorage.setItem(
        "render0x-theme",
        themeName
    );
}


/* Load saved theme on every page */

const savedTheme =
    localStorage.getItem("render0x-theme") || "purple";

applyRender0XTheme(savedTheme);
