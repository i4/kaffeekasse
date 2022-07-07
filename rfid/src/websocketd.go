package main

import (
	"bufio"
	"context"
	"io"
	"log"
	"net/http"
	"os"
	"os/exec"
	"time"

	"nhooyr.io/websocket"
)

type Request struct {
	ws   *websocket.Conn
	ctx  context.Context
	time time.Time
}

func dpms(mode string) {
	xset := exec.Command("xset", "dpms", "force", mode)
	xset.Env = append(os.Environ(), "DISPLAY=:0")
	err := xset.Run()
	if err != nil {
		log.Print(err)
	}
}

func filter(channel chan Request, command string, arg ...string) error {
	filter := exec.Command(command, arg...)
	in, err := filter.StdinPipe()
	if err != nil {
		return err
	}
	filter.Stderr = os.Stderr
	out, err := filter.StdoutPipe()
	if err != nil {
		return err
	}

	err = filter.Start()
	if err != nil {
		return err
	}

	scanner := bufio.NewScanner(out)
	abort := make(chan error)
	go func() {
		abort <- filter.Wait()
	}()

	last := time.Now()
	for {
		select {
		case rq := <-channel:
			// On multiple pending websocket request, send the
			// same token to all waiting requests. If the first
			// request is canceled, the others would not get a
			// response (before the filter returns a new one).
			if scanner.Text() == "" || rq.time.After(last) {
				_, err := io.WriteString(in, "\n")
				if err != nil {
					rq.ws.Close(websocket.StatusInternalError, "write failed")
					continue
				} else if scanner.Scan() {
					last = time.Now()
					go dpms("on") // enable display on reception
				} else {
					rq.ws.Close(websocket.StatusInternalError, "read failed")
					continue
				}
			}

			msg := scanner.Text() // copy for go routine
			go func() {
				err := rq.ws.Write(rq.ctx, websocket.MessageText, []byte(msg))
				if err != nil {
					select {
					case <-rq.ctx.Done():

					default:
						log.Println("filter: could not reply:", err)
					}
				}
			}()

		case err := <-abort:
			return err
		}
	}
}

func main() {
	/* TODO: Arguments for port, listen-address, ...? */
	channel := make(chan Request)
	srv := &http.Server{Addr: "127.0.0.1:8000"}

	/* use default filter */
	if len(os.Args) <= 1 {
		log.Fatalf("usage: %s <command...>", os.Args[0])
	}
	/* remaining arguments are used as filter command */
	cmd := os.Args[1:]

	go func() {
		for {
			err := filter(channel, cmd[0], cmd[1:]...)
			log.Printf("filter: %s", err)
		}
	}()

	http.HandleFunc("/getuid", func(w http.ResponseWriter, r *http.Request) {
		ws, err := websocket.Accept(w, r, &websocket.AcceptOptions{
			Subprotocols:       []string{"getuid"},
			InsecureSkipVerify: true,
		})
		if err != nil {
			log.Printf("upgrade: %s", err)
			return
		}
		ctx := r.Context()
		for {
			typ, data, err := ws.Read(ctx)
			if err != nil {
				if websocket.CloseStatus(err) != websocket.StatusGoingAway {
					log.Printf("websocket: %s", err)
				}
				return
			} else if typ != websocket.MessageText {
				ws.Close(websocket.StatusUnsupportedData, "only plaintext allowed")
				return
			} else if string(data) != "version 1.0" {
				ws.Close(websocket.StatusUnsupportedData, "only version 1.0 is supported")
				return
			} else {
				// go func because of library requires regular
				// calls to ws.Read (websocket ping-pong)
				go func() {
					channel <- Request{ws, ctx, time.Now()}
				}()
			}
		}
	})
	err := srv.ListenAndServe()
	log.Fatal("ListenAndServe: ", err)
}
