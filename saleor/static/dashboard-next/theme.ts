import { createMuiTheme, Theme } from "@material-ui/core/styles";
import { fade } from "@material-ui/core/styles/colorManipulator";

const createShadow = (pv, pb, ps, uv, ub, us, av, ab, as) =>
  [
    `0 ${pv}px ${pb}px ${ps}px rgba(0, 0, 0, 0.2)`,
    `0 ${uv}px ${ub}px ${us}px rgba(0, 0, 0, 0.14)`,
    `0 ${av}px ${ab}px ${as}px rgba(0, 0, 0, 0.12)`
  ].join(",");

export const ICONBUTTON_SIZE = 48;

export type IThemeColors = Record<
  "primary" | "secondary" | "error" | "paperBorder" | "autofill",
  string
> & {
  background: Record<"default" | "paper", string>;
} & {
  font: Record<"default" | "gray", string>;
} & {
  gray: Record<"default" | "disabled", string>;
};

const fontFamily = '"Inter", "roboto", "sans-serif"';

export default (colors: IThemeColors): Theme =>
  createMuiTheme({
    overrides: {
      MuiButton: {
        contained: {
          "&$disabled": {
            backgroundColor: fade(colors.primary, 0.12)
          }
        },
        label: {
          fontWeight: 600
        },
        root: {
          "& svg": {
            marginLeft: 8
          },
          borderRadius: 8
        }
      },
      MuiCard: {
        root: {
          borderColor: colors.paperBorder,
          borderRadius: 8,
          boxShadow: "none"
        }
      },
      MuiCardActions: {
        root: {
          flexDirection: "row-reverse" as "row-reverse"
        }
      },
      MuiInput: {
        input: {
          "&:-webkit-autofill": {
            WebkitTextFillColor: colors.font.default,
            boxShadow: `inset 0 0 0px 9999px ${colors.autofill}`
          },
          "&::placeholder": {
            opacity: "initial !important" as "initial"
          }
        },
        underline: {
          "&:after": {
            borderBottomColor: colors.primary
          }
        }
      },
      MuiInputBase: {
        input: {
          "&::placeholder": {
            color: colors.font.gray
          }
        }
      },
      MuiInputLabel: {
        formControl: {
          transform: "translate(0, 1.5px) scale(0.75)",
          transformOrigin: "top left" as "top left",
          width: "100%"
        },
        root: {
          color: [[colors.primary], "!important"] as any
        },
        shrink: {
          // Negates x0.75 scale
          width: "133%"
        }
      },
      MuiMenu: {
        paper: {
          borderRadius: 8
        }
      },
      MuiSwitch: {
        bar: {
          "$colorPrimary$checked + &": {
            backgroundColor: colors.primary
          },
          backgroundColor: colors.gray.default,
          borderRadius: 12,
          height: 24,
          marginTop: -12,
          opacity: [["1"], "!important"] as any,
          width: 48
        },
        checked: {
          transform: "translateX(24px)"
        },
        disabled: {
          "&$switchBase": {
            "& + $bar": {
              backgroundColor: colors.gray.disabled
            }
          }
        },
        icon: {
          backgroundColor: colors.background.paper,
          boxShadow: "none",
          marginLeft: 4
        },
        iconChecked: {
          backgroundColor: colors.background.paper,
          boxShadow: "none"
        }
      },
      MuiTable: {
        root: {
          fontFamily,
          fontFeatureSettings: '"tnum"'
        }
      },
      MuiTableCell: {
        body: {
          fontSize: ".875rem",
          paddingBottom: 8,
          paddingTop: 8
        },
        head: {
          fontSize: ".875rem",
          fontWeight: 400
        },
        paddingCheckbox: {
          width: 72
        },
        root: {
          "&:first-child": {
            "&:not($paddingCheckbox)": {
              paddingLeft: 24 + "px",
              textAlign: "left" as "left"
            }
          },
          borderBottomColor: colors.paperBorder,
          height: 56,
          padding: "4px 24px 4px 0"
        }
      },
      MuiTableRow: {
        footer: {
          "$root$hover&:hover": {
            background: "none"
          }
        },
        head: {
          "$root$hover&:hover": {
            background: "none"
          }
        },
        hover: {
          "$root&:hover": {
            backgroundColor: fade(colors.primary, 0.2)
          }
        },
        root: {
          "&$selected": {
            backgroundColor: fade(colors.primary, 0.05)
          }
        }
      }
    },
    palette: {
      background: colors.background,
      error: {
        main: colors.error
      },
      primary: {
        contrastText: "#ffffff",
        main: colors.primary
      },
      secondary: {
        contrastText: "#ffffff",
        main: colors.secondary
      },
      text: {
        disabled: colors.font.gray,
        hint: colors.font.gray,
        primary: colors.font.default,
        secondary: colors.font.gray
      }
    },
    shadows: [
      "none",
      createShadow(1, 1, 0, 2, 1, -2, 1, 3, 0),
      createShadow(2, 2, 0, 3, 1, -2, 1, 5, 0),
      createShadow(3, 4, 0, 3, 3, -2, 1, 8, 0),
      createShadow(4, 5, 0, 1, 10, 0, 2, 4, -1),
      createShadow(5, 8, 0, 1, 14, 0, 3, 4, -1),
      createShadow(6, 10, 0, 1, 18, 0, 3, 5, -1),
      createShadow(7, 10, 0, 2, 16, 1, 4, 5, -2),
      createShadow(8, 10, 1, 3, 14, 2, 5, 5, -3),
      createShadow(9, 12, 1, 3, 16, 3, 5, 6, -4),
      createShadow(10, 14, 1, 4, 18, 3, 6, 7, -4),
      createShadow(11, 16, 1, 4, 20, 3, 6, 7, -4),
      createShadow(12, 17, 1, 5, 22, 4, 7, 8, -4),
      createShadow(13, 19, 1, 5, 24, 4, 7, 8, -4),
      createShadow(14, 21, 1, 5, 26, 4, 7, 9, -5),
      createShadow(15, 22, 1, 5, 28, 4, 7, 9, -5),
      createShadow(16, 24, 2, 6, 30, 5, 8, 10, -5),
      createShadow(15, 27, 3, 7, 28, 3, 10, 14, -4),
      createShadow(14, 30, 4, 8, 26, 1, 12, 17, -3),
      createShadow(13, 33, 4, 8, 24, -1, 14, 20, -1),
      createShadow(12, 36, 5, 9, 22, -2, 16, 24, 1),
      createShadow(11, 39, 6, 10, 20, -4, 18, 28, 1),
      createShadow(10, 41, 7, 10, 18, -5, 20, 31, 2),
      createShadow(9, 44, 7, 11, 16, -6, 22, 35, 2),
      createShadow(9, 46, 8, 11, 15, -7, 24, 38, 3)
    ],
    typography: {
      allVariants: {
        fontFamily
      },
      body1: {
        fontSize: "1rem"
      },
      body2: {
        fontSize: "0.75rem",
        fontWeight: 600 as 600
      },
      display1: {
        color: colors.font.default
      },
      headline: {
        fontSize: "1.3125rem"
      }
    }
  });
