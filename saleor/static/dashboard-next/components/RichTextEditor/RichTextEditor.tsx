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
import LinkIcon from "@material-ui/icons/Link";
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
import LinkEntity from "./LinkEntity";
import LinkSource from "./LinkSource";

export interface RichTextEditorProps {
  disabled: boolean;
  label: string;
  name: string;
  initial?: RawDraftContentState;
  onChange: (event: React.ChangeEvent<any>) => void;
}

const styles = (theme: Theme) =>
  createStyles({
    label: {
      marginBottom: theme.spacing.unit * 2
    },
    root: {
      "& .DraftEditor": {
        "&-editorContainer": {
          "& a": {
            color: theme.palette.secondary.light
          },
          "&:after": {
            background: theme.palette.primary.main,
            bottom: -1,
            content: "''",
            display: "block",
            height: 2,
            position: "absolute",
            transform: "scaleX(0)",
            transition: theme.transitions.duration.short + "ms",
            width: "100%"
          },
          "&:hover": {
            borderBottom: ``
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
                  transform: "scaleX(1)"
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
      }
    }
  });
const RichTextEditor = withStyles(styles, { name: "RichTextEditor" })(
  ({
    classes,
    initial,
    label,
    name,
    onChange
  }: RichTextEditorProps & WithStyles<typeof styles>) => (
    <div className={classes.root}>
      <Typography className={classes.label} variant="caption" color="primary">
        {label}
      </Typography>
      <DraftailEditor
        key={JSON.stringify(initial)}
        rawContentState={initial || null}
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
        ]}
      />
    </div>
  )
);
RichTextEditor.displayName = "RichTextEditor";
export default RichTextEditor;
