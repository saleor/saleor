import { createMuiTheme } from "material-ui/styles/index";
import grey from "material-ui/colors/grey";

const transition = "200ms";
export default createMuiTheme({
  palette: {
    primary: {
      main: "#2bb673"
    },
    secondary: {
      main: "#26A5D4"
    }
  },
  typography: {
    htmlFontSize: 16,
    fontFamily: "Roboto, sans-serif"
  },
  overrides: {
    MuiButton: {
      root: {
        fontWeight: 400,
        fontSize: "0.875rem"
      },
      raised: {
        color: "#ffffff !important"
      }
    },
    MuiTableCell: {
      root: {
        paddingRight: "1.5rem !important",
        "&:first-child": {
          whiteSpace: "nowrap"
        }
      },
      typeHead: {
        fontWeight: 400
      }
    },
    // MuiTextField: {
    //   inkbar: {
    //     "&:after": {
    //       backgroundColor: "#26A5D4"
    //     }
    //   }
    // },
    MuiInput: {
      root: {
        fontSize: "0.875rem"
      }
    },
    MuiFormLabel: {
      root: {
        fontSize: "0.875rem"
      }
    },
    MuiPaper: {
      root: {
        marginTop: "1rem"
      }
    },
    MuiCardActions: {
      root: {
        borderTop: `1px solid ${grey[300]}`,
        margin: "24px -16px -24px",
        padding: "0 8px",
        "@media (max-width: 480px)": {
          padding: "32px 8px"
        }
      }
    },
    MuiTableRow: {
      root: {
        transition,
        "&:hover": {
          backgroundColor: grey[100]
        }
      },
      typeHead: {
        "&:hover": {
          backgroundColor: "inherit"
        }
      },
      typeFooter: {
        "&:hover": {
          backgroundColor: "inherit"
        }
      }
    },
    MuiCircularProgress: {
      root: {
        display: "block",
        margin: "0 auto"
      }
    },
    MuiTypography: {
      display1: {
        fontSize: "1.5rem",
        marginBottom: "1rem",
        fontWeight: 300,
        color: "#000000"
      },
      title: {
        fontSize: "1rem",
        fontWeight: 400,
        marginBottom: ".75rem"
      }
    }
  }
});
