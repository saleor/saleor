import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import { fade } from "@material-ui/core/styles/colorManipulator";
import Typography from "@material-ui/core/Typography";
import classNames from "classnames";
import { RawDraftContentState } from "draft-js";
import {
  BLOCK_TYPE,
  DraftailEditor,
  ENTITY_TYPE,
  INLINE_STYLE
} from "draftail";
import isEqual from "lodash-es/isEqual";
import React from "react";

import BoldIcon from "../../icons/BoldIcon";
import HeaderOne from "../../icons/HeaderOne";
import HeaderThree from "../../icons/HeaderThree";
import HeaderTwo from "../../icons/HeaderTwo";
import ItalicIcon from "../../icons/ItalicIcon";
import LinkIcon from "../../icons/LinkIcon";
import OrderedListIcon from "../../icons/OrderedListIcon";
import QuotationIcon from "../../icons/QuotationIcon";
import StrikethroughIcon from "../../icons/StrikethroughIcon";
import UnorderedListIcon from "../../icons/UnorderedListIcon";

// import ImageEntity from "./ImageEntity";
// import ImageSource from "./ImageSource";
import { ChangeEvent } from "@saleor/hooks/useForm";
import LinkEntity from "./LinkEntity";
import LinkSource from "./LinkSource";

export interface RichTextEditorProps {
  disabled: boolean;
  error: boolean;
  helperText: string;
  label: string;
  name: string;
  scroll?: boolean;
  initial?: RawDraftContentState;
  onChange: (event: React.ChangeEvent<any>) => void;
}

const styles = (theme: Theme) =>
  createStyles({
    error: {
      color: theme.palette.error.main
    },
    helperText: {
      marginTop: theme.spacing.unit * 0.75
    },
    input: {
      position: "relative"
    },
    label: {
      fontSize: theme.typography.caption.fontSize,
      left: 12,
      position: "absolute",
      top: 9
    },
    linkIcon: {
      marginTop: 2
    },
    root: {
      "& .DraftEditor": {
        "&-editorContainer": {
          "& .public-DraftEditor-content": {
            lineHeight: 1.62
          },
          "& a": {
            color: theme.palette.primary.light
          },
          "&:after": {
            background: theme.palette.getContrastText(
              theme.palette.background.default
            ),
            bottom: -11,
            content: "''",
            display: "block",
            height: 2,
            left: -12,
            position: "absolute",
            transform: "scaleX(0) scaleY(0)",
            width: "calc(100% + 24px)"
          },
          position: "relative"
        },
        "&-root": {
          ...theme.typography.body2
        }
      },
      "& .Draftail": {
        "&-Editor": {
          "&--focus": {
            borderColor: theme.palette.common.white,
            boxShadow: `inset 0px 0px 0px 2px ${theme.palette.primary.main}`
          },
          "&:hover": {
            borderColor: theme.palette.primary.main
          },
          border: `1px rgba(0, 0, 0, 0.23) solid`,
          borderTopLeftRadius: 4,
          borderTopRightRadius: 4,
          padding: "27px 12px 10px",
          position: "relative",
          transition: theme.transitions.duration.shortest + "ms"
        },
        "&-Toolbar": {
          "&Button": {
            "& svg": {
              padding: 2
            },
            "&--active": {
              "&:hover": {
                background: theme.palette.primary.main
              },
              "&:not(:hover)": {
                borderRightColor: theme.palette.primary.main
              },
              background: theme.palette.primary.main
            },
            "&:focus": {
              "&:active": {
                "&:after": {
                  background: fade(theme.palette.primary.main, 0.3),
                  borderRadius: "100%",
                  content: "''",
                  display: "block",
                  height: "100%",
                  width: "100%"
                }
              }
            },
            "&:hover": {
              background: fade(theme.palette.primary.main, 0.3)
            },
            alignItems: "center",
            background: "none",
            border: "none",
            borderRight: `1px ${
              theme.overrides.MuiCard.root.borderColor
            } solid`,
            color: theme.typography.body2.color,
            cursor: "pointer",
            display: "inline-flex",
            height: 36,
            justifyContent: "center",
            padding: theme.spacing.unit + 2,
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
          background: theme.palette.background.default,
          border: `1px ${theme.overrides.MuiCard.root.borderColor} solid`,
          display: "inline-flex",
          flexWrap: "wrap",
          marginBottom: theme.spacing.unit,
          marginTop: 10,
          [theme.breakpoints.down(460)]: {
            width: "min-content"
          }
        },
        "&-block": {
          "&--blockquote": {
            borderLeft: `2px solid ${theme.overrides.MuiCard.root.borderColor}`,
            margin: 0,
            padding: `${theme.spacing.unit}px ${theme.spacing.unit * 2}px`
          }
        }
      },
      "&$error": {
        "& .Draftail": {
          "&-Editor": {
            borderColor: theme.palette.error.main
          }
        }
      }
    },
    scroll: {
      "& .DraftEditor": {
        "&-editorContainer": {
          "& .public-DraftEditor-content": {
            lineHeight: 1.62
          }
        }
      }
    },
    smallIcon: {
      marginLeft: 10
    }
  });

function handleSave(
  value: any,
  initial: any,
  name: string,
  onChange: (event: ChangeEvent) => void
) {
  if (value && !isEqual(value, initial)) {
    onChange({
      target: {
        name,
        value
      }
    });
  }
}

const RichTextEditor = withStyles(styles, { name: "RichTextEditor" })(
  ({
    classes,
    error,
    helperText,
    initial,
    label,
    name,
    scroll,
    onChange
  }: RichTextEditorProps & WithStyles<typeof styles>) => (
    <div
      className={classNames({
        [classes.error]: error,
        [classes.root]: true,
        [classes.scroll]: scroll
      })}
    >
      <div className={classes.input}>
        <Typography className={classes.label} variant="caption" color="primary">
          {label}
        </Typography>
        <DraftailEditor
          key={JSON.stringify(initial)}
          rawContentState={
            initial && Object.keys(initial).length > 0 ? initial : null
          }
          onSave={value => handleSave(value, initial, name, onChange)}
          blockTypes={[
            {
              icon: <HeaderOne />,
              type: BLOCK_TYPE.HEADER_ONE
            },
            { icon: <HeaderTwo />, type: BLOCK_TYPE.HEADER_TWO },
            { icon: <HeaderThree />, type: BLOCK_TYPE.HEADER_THREE },
            { icon: <QuotationIcon />, type: BLOCK_TYPE.BLOCKQUOTE },
            {
              icon: <UnorderedListIcon />,
              type: BLOCK_TYPE.UNORDERED_LIST_ITEM
            },
            { icon: <OrderedListIcon />, type: BLOCK_TYPE.ORDERED_LIST_ITEM }
          ]}
          inlineStyles={[
            {
              icon: <BoldIcon className={classes.smallIcon} />,
              type: INLINE_STYLE.BOLD
            },
            {
              icon: <ItalicIcon className={classes.smallIcon} />,
              type: INLINE_STYLE.ITALIC
            },
            {
              icon: <StrikethroughIcon />,
              type: INLINE_STYLE.STRIKETHROUGH
            }
          ]}
          enableLineBreak
          entityTypes={[
            {
              attributes: ["url"],
              decorator: LinkEntity,
              icon: <LinkIcon className={classes.linkIcon} />,
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
      </div>
      {helperText && (
        <Typography
          className={classNames({
            [classes.error]: error,
            [classes.helperText]: true
          })}
          variant="caption"
        >
          {helperText}
        </Typography>
      )}
    </div>
  )
);
RichTextEditor.displayName = "RichTextEditor";
RichTextEditor.defaultProps = {
  scroll: true
};
export default RichTextEditor;
