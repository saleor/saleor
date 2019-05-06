import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import CardActions from "@material-ui/core/CardActions";
import Paper from "@material-ui/core/Paper";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import classNames from "classnames";
import * as React from "react";
import SortableTree, { NodeRendererProps } from "react-sortable-tree";

import CardTitle from "../../../components/CardTitle";
import useTheme from "../../../hooks/useTheme";
import i18n from "../../../i18n";
import Draggable from "../../../icons/Draggable";
import { MenuDetails_menu_items } from "../../types/MenuDetails";
import {
  getDiff,
  getNodeData,
  getNodeQuantity,
  TreeNode,
  TreePermutation
} from "./tree";

const NODE_HEIGHT = 56;
const NODE_MARGIN = 40;

export interface MenuItemsProps {
  items: MenuDetails_menu_items[];
  onChange: (operation: TreePermutation) => void;
}

const styles = (theme: Theme) =>
  createStyles({
    actions: {
      flexDirection: "row"
    },
    container: {
      background: theme.palette.grey[200]
    },
    darkContainer: {
      background: `${theme.palette.grey[800]} !important`
    },
    dragIcon: {
      cursor: "grab"
    },
    nodeTitle: {
      marginLeft: theme.spacing.unit * 7
    },
    root: {
      "& .rst__collapseButton": {
        display: "none"
      },
      "& .rst__node": {
        height: "auto !important"
      }
    },
    row: {
      alignItems: "center",
      background: theme.palette.background.paper,
      borderBottom: `1px ${theme.overrides.MuiCard.root.borderColor} solid`,
      borderRadius: 0,
      display: "flex",
      flexDirection: "row",
      height: NODE_HEIGHT,
      justifyContent: "flex-start",
      paddingLeft: theme.spacing.unit * 3
    },
    rowContainer: {
      "& > *": {
        opacity: 1,
        transition: `opacity ${theme.transitions.duration.standard}ms`
      },
      transition: `margin ${theme.transitions.duration.standard}ms`
    },
    rowContainerDragged: {
      "&$rowContainer": {
        "& > *": {
          opacity: 0
        },
        "&:before": {
          background: theme.palette.background.paper,
          border: `1px solid ${theme.palette.primary.main}`,
          borderRadius: "100%",
          content: "''",
          height: 7,
          left: 0,
          position: "absolute",
          top: -3,
          width: 7
        },
        borderTop: `1px solid ${theme.palette.primary.main}`,
        height: 0,
        position: "relative",
        top: -1
      }
    },
    rowContainerPlaceholder: {
      borderRadius: 8,
      width: 300
    }
  });

class Node extends React.Component<NodeRendererProps> {
  render() {
    return <NodeComponent {...this.props} key={this.props.node.id} />;
  }
}

const NodeComponent = withStyles(styles, {
  name: "NodeComponent"
})(
  ({
    classes,
    node,
    path,
    connectDragPreview,
    connectDragSource,
    isDragging
  }: NodeRendererProps & WithStyles<typeof styles>) => {
    const draggedClassName = classNames(
      classes.rowContainer,
      classes.rowContainerDragged
    );
    const defaultClassName = isDragging
      ? draggedClassName
      : classes.rowContainer;
    const placeholderClassName = classNames(
      classes.rowContainer,
      classes.rowContainerPlaceholder
    );

    const [className, setClassName] = React.useState(defaultClassName);
    React.useEffect(() => setClassName(defaultClassName), [isDragging]);

    const handleDragStart = () => {
      setClassName(placeholderClassName);
      setTimeout(() => setClassName(defaultClassName), 0);
    };

    return connectDragPreview(
      <div
        className={className}
        style={{
          marginLeft: NODE_MARGIN * (path.length - 1)
        }}
      >
        <Paper className={classes.row} elevation={0}>
          {connectDragSource(
            <div onDragStart={handleDragStart}>
              <Draggable className={classes.dragIcon} />
            </div>
          )}
          <Typography className={classes.nodeTitle}>{node.title}</Typography>
        </Paper>
      </div>
    );
  }
);

const MenuItems = withStyles(styles, { name: "MenuItems" })(
  ({
    classes,
    items,
    onChange
  }: MenuItemsProps & WithStyles<typeof styles>) => {
    const { isDark } = useTheme();

    return (
      <Card>
        <CardTitle title={i18n.t("Menu Items")} />
        <div
          className={classNames(classes.container, {
            [classes.darkContainer]: isDark
          })}
          style={{ minHeight: (getNodeQuantity(items) - 0.5) * NODE_HEIGHT }}
        >
          <SortableTree
            className={classes.root}
            generateNodeProps={({ path }) => ({
              className: classes.row,
              style: {
                marginLeft: NODE_MARGIN * (path.length - 1)
              }
            })}
            isVirtualized={false}
            rowHeight={NODE_HEIGHT}
            treeData={items.map(getNodeData)}
            theme={{
              nodeContentRenderer: Node
            }}
            onChange={newTree =>
              onChange(getDiff(items.map(getNodeData), newTree as TreeNode[]))
            }
          />
        </div>
        <CardActions className={classes.actions}>
          <Button color="primary">
            {i18n.t("Add new item", {
              context: "add menu item"
            })}
          </Button>
        </CardActions>
      </Card>
    );
  }
);
MenuItems.displayName = "MenuItems";
export default MenuItems;
