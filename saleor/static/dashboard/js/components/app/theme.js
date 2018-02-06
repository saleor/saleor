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
        fontSize: '1rem !important'
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
    }
  }
});
