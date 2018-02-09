import { createMuiTheme } from 'material-ui/styles/index';

export default createMuiTheme({
  palette: {
    primary: {
      main: '#2bb673'
    },
    secondary: {
      main: '#26A5D4'
    }
  },
  overrides: {
    MuiButton: {
      root: {
        fontWeight: 400,
        fontSize: '1rem'
      },
      raised: {
        color: '#ffffff !important'
      }
    },
    MuiTableCell: {
      root: {
        fontSize: '1rem !important',
        '&:first-child': {
          whiteSpace: 'nowrap'
        }
      },
      typeHead: {
        fontSize: '.9rem !important',
        fontWeight: 400
      }
    },
    MuiTextField: {
      inkbar: {
        '&:after': {
          backgroundColor: '#26A5D4'
        }
      }
    },
    MuiCardActions: {
      root: {
        borderTop: '1px solid rgba(160, 160, 160, 0.2)',
        margin: '24px -16px -24px',
        padding: '0 8px'
      }
    }
  }
});
