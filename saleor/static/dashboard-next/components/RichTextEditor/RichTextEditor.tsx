import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import { fade } from "@material-ui/core/styles/colorManipulator";
import Typography from "@material-ui/core/Typography";
import BoldIcon from "@material-ui/icons/FormatBold";
import ItalicIcon from "@material-ui/icons/FormatItalic";
import UnorderedListIcon from "@material-ui/icons/FormatListBulleted";
import OrderedListIcon from "@material-ui/icons/FormatListNumbered";
import QuotationIcon from "@material-ui/icons/FormatQuote";
// import ImageIcon from "@material-ui/icons/Image";
import LinkIcon from "@material-ui/icons/Link";
import * as classNames from "classnames";
import { RawDraftContentState } from "draft-js";
import {
  BLOCK_TYPE,
  DraftailEditor,
  ENTITY_TYPE,
  INLINE_STYLE
} from "draftail";
import * as React from "react";

import HeaderThree from "../../icons/HeaderThree";
import HeaderTwo from "../../icons/HeaderTwo";
// import ImageEntity from "./ImageEntity";
// import ImageSource from "./ImageSource";
import LinkEntity from "./LinkEntity";
import LinkSource from "./LinkSource";

export interface RichTextEditorProps {
  disabled: boolean;
  error: boolean;
  helperText: string;
  label: string;
  name: string;
  initial?: RawDraftContentState;
  onChange: (event: React.ChangeEvent<any>) => void;
}

const styles = (theme: Theme) =>
  createStyles({
    "@keyframes focus": {
      from: {
        transform: "scaleX(0) scaleY(1)"
      },
      to: {
        transform: "scaleX(1) scaleY(1)"
      }
    },
    "@keyframes hover": {
      from: {
        transform: "scaleX(1) scaleY(0)"
      },
      to: {
        transform: "scaleX(1) scaleY(1)"
      }
    },
    error: {
      color: theme.palette.error.main
    },
    helperText: {
      marginTop: theme.spacing.unit * 0.75
    },
    label: {
      marginBottom: theme.spacing.unit * 2
    },
    root: {
      "& .DraftEditor": {
        "&-editorContainer": {
          "& .public-DraftEditor-content": {
            lineHeight: 1.62,
            maxHeight: 300,
            minHeight: 100,
            overflowY: "scroll"
          },
          "& a": {
            color: theme.palette.secondary.light
          },
          "&:after": {
            animationDuration: theme.transitions.duration.shortest + "ms",
            animationFillMode: "both",
            background: theme.palette.grey[700],
            bottom: -1,
            content: "''",
            display: "block",
            height: 2,
            position: "absolute",
            transform: "scaleX(0) scaleY(0)",
            width: "100%"
          },
          "&:hover": {
            "&:after": {
              animationName: "hover"
            }
          },
          borderBottom: `1px ${theme.palette.grey[500]} solid`,
          paddingBottom: theme.spacing.unit / 2,
          position: "relative"
        },
        "&-root": {
          ...theme.typography.body1
        }
      },
      "& .Draftail": {
        "&-Editor": {
          "&--focus": {
            "& .DraftEditor": {
              "&-editorContainer": {
                "&:after": {
                  animationName: "focus !important",
                  background: theme.palette.primary.main,
                  transform: "scaleX(0) scaleY(1)"
                }
              }
            }
          }
        },
        "&-Toolbar": {
          "&Button": {
            "&--active": {
              "&:hover": {
                background: theme.palette.secondary.main
              },
              "&:not(:hover)": {
                borderRightColor: theme.palette.secondary.main
              },
              background: theme.palette.secondary.main
            },
            "&:focus": {
              "&:active": {
                "&:after": {
                  background: fade(theme.palette.secondary.main, 0.3),
                  borderRadius: "100%",
                  content: "''",
                  display: "block",
                  height: "100%",
                  width: "100%"
                }
              }
            },
            "&:hover": {
              background: fade(theme.palette.secondary.main, 0.3)
            },
            alignItems: "center",
            background: "none",
            border: "none",
            borderRight: `1px ${theme.palette.grey[300]} solid`,
            cursor: "pointer",
            display: "inline-flex",
            height: 36,
            justifyContent: "center",
            padding: theme.spacing.unit - 1,
            transition: theme.transitions.duration.short + "ms",
            width: 36
          },
          "&Group": {
            "&:last-of-type": {
              "& .Draftail-ToolbarButton": {
                "&:last-of-type": {
                  border: "none"
                }
              }
            },
            display: "flex"
          },
          border: `1px ${theme.palette.grey[300]} solid`,
          display: "inline-flex",
          marginBottom: theme.spacing.unit
        },
        "&-block": {
          "&--blockquote": {
            borderLeft: `2px solid ${theme.palette.grey[300]}`,
            margin: 0,
            padding: `${theme.spacing.unit}px ${theme.spacing.unit * 2}px`
          }
        }
      },

      "&$error": {
        "& .Draftail": {
          "&-Editor": {
            "& .DraftEditor": {
              "&-editorContainer": {
                "&:after": {
                  animationName: "none",
                  background: theme.palette.error.main,
                  transform: "scaleX(1) scaleY(1)"
                }
              }
            },
            "&--focus": {
              "& .DraftEditor": {
                "&-editorContainer": {
                  "&:after": {
                    animationName: "none !important"
                  }
                }
              }
            }
          }
        }
      }
    }
  });
const RichTextEditor = withStyles(styles, { name: "RichTextEditor" })(
  ({
    classes,
    error,
    helperText,
    initial,
    label,
    name,
    onChange
  }: RichTextEditorProps & WithStyles<typeof styles>) => (
    <div
      className={classNames({
        [classes.error]: error,
        [classes.root]: true
      })}
    >
      <Typography className={classes.label} variant="caption" color="primary">
        {label}
      </Typography>
      <DraftailEditor
        key={JSON.stringify(initial)}
        rawContentState={
          initial && Object.keys(initial).length > 0 ? initial : null
        }
        onSave={value =>
          onChange({
            target: {
              name,
              value
            }
          } as any)
        }
        blockTypes={[
          { icon: <HeaderTwo />, type: BLOCK_TYPE.HEADER_TWO },
          { icon: <HeaderThree />, type: BLOCK_TYPE.HEADER_THREE },
          { icon: <QuotationIcon />, type: BLOCK_TYPE.BLOCKQUOTE },
          { icon: <UnorderedListIcon />, type: BLOCK_TYPE.UNORDERED_LIST_ITEM },
          { icon: <OrderedListIcon />, type: BLOCK_TYPE.ORDERED_LIST_ITEM }
        ]}
        inlineStyles={[
          { icon: <BoldIcon />, type: INLINE_STYLE.BOLD },
          { icon: <ItalicIcon />, type: INLINE_STYLE.ITALIC }
        ]}
        enableLineBreak
        entityTypes={[
          {
            attributes: ["href"],
            decorator: LinkEntity,
            icon: <LinkIcon />,
            source: LinkSource,
            type: ENTITY_TYPE.LINK
          }
          // {
          //   attributes: ["href"],
          //   decorator: ImageEntity,
          //   icon: <ImageIcon />,
          //   source: ImageSource,
          //   type: ENTITY_TYPE.IMAGE
          // }
        ]}
      />
      <Typography
        className={classNames({
          [classes.error]: error,
          [classes.helperText]: true
        })}
        variant="caption"
      >
        {helperText}
      </Typography>
    </div>
  )
);
RichTextEditor.displayName = "RichTextEditor";
export default RichTextEditor;
