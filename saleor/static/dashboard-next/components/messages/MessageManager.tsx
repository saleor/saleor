import Button from "@material-ui/core/Button";
import IconButton from "@material-ui/core/IconButton";
import Snackbar from "@material-ui/core/Snackbar";
import CloseIcon from "@material-ui/icons/Close";
import * as React from "react";

import { IMessage, MessageContext } from "./";

interface Message extends IMessage {
  key: string;
}
interface MessageManagerProps {}
interface MessageManagerState {
  message: Message;
  opened: boolean;
}

export class MessageManager extends React.Component<
  MessageManagerProps,
  MessageManagerState
> {
  state = {
    message: null,
    opened: false
  };
  queue = [];

  handleClose = (event, reason) => {
    if (reason === "clickaway") {
      return;
    }
    this.setState({ open: false });
  };

  handleExited = () => {
    this.processQueue();
  };

  pushMessage = (message: Message) => {
    this.queue.push({
      key: new Date().getTime(),
      message
    });

    if (this.state.opened) {
      this.setState({ open: false });
    } else {
      this.processQueue();
    }
  };

  processQueue = () => {
    if (this.queue.length > 0) {
      this.setState({
        message: this.queue.shift(),
        opened: true
      });
    }
  };

  render() {
    const { text, key } = this.state.message;
    return (
      <>
        <Snackbar
          key={key}
          anchorOrigin={{
            vertical: "top",
            horizontal: "right"
          }}
          open={this.state.opened}
          autoHideDuration={6000}
          onClose={this.handleClose}
          onExited={this.handleExited}
          ContentProps={{
            "aria-describedby": "message-id"
          }}
          message={<span id="message-id">{text}</span>}
          action={[
            <Button
              key="undo"
              color="secondary"
              size="small"
              onClick={this.handleClose}
            >
              UNDO
            </Button>,
            <IconButton
              key="close"
              aria-label="Close"
              color="inherit"
              className={classes.close}
              onClick={this.handleClose}
            >
              <CloseIcon />
            </IconButton>
          ]}
        />
        <MessageContext.Provider value={this.pushMessage}>
          {this.props.children}
        </MessageContext.Provider>
      </>
    );
  }
}
export default MessageManager;
