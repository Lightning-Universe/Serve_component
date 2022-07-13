package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"net/http"
	"net/http/httputil"
	"strconv"
	"sync"
	"time"

	"github.com/gorilla/mux"
	"github.com/jmcvetta/randutil"
)

type ProxyRouter struct {
	routing   []map[string][]string
	routingMu *sync.RWMutex
}

func (p *ProxyRouter) UpdateRouting(decoder *json.Decoder) {
	p.routingMu.Lock()
	decoder.Decode(&p.routing)
	fmt.Println(p.routing)
	p.routingMu.Unlock()
}

func (p *ProxyRouter) GetHost() []string {
	p.routingMu.RLock()
	defer p.routingMu.RUnlock()
	out := make([]string, 0, 1)
	for _, router := range p.routing {
		choices := make([]randutil.Choice, 0, len(router))
		for prob, urls := range router {
			prob, _ := strconv.Atoi(prob)
			choice := randutil.Choice{
				Weight: int(prob),
				Item:   urls,
			}
			choices = append(choices, choice)
		}
		result, _ := randutil.WeightedChoice(choices)
		var _, _ = result.Item.([]string)
	}
	return out
}

func main() {
	host := flag.String("host", "0.0.0.0", "Address of the server")
	port := flag.String("port", "8000", "Port of the server")

	reverseProxy := &httputil.ReverseProxy{}
	proxyRouter := &ProxyRouter{
		routingMu: &sync.RWMutex{},
	}

	reverseProxy.Director = func(r *http.Request) {
		r.URL.Host = proxyRouter.GetHost()[0]
	}

	// https://github.com/gorilla/mux
	r := mux.NewRouter()
	r.HandleFunc("/api/v1/proxy", func(w http.ResponseWriter, r *http.Request) {
		decoder := json.NewDecoder(r.Body)
		proxyRouter.UpdateRouting(decoder)
	})

	r.PathPrefix("/", reverseProxy)

	srv := &http.Server{
		Handler: r,
		Addr:    fmt.Sprintf("%s:%s", *host, *port),
		// Good practice: enforce timeouts for servers you create
		WriteTimeout: 15 * time.Second,
		ReadTimeout:  15 * time.Second,
	}

	_ = srv.ListenAndServe()
}

// func (p *ProxyRouter) GetHost() []string {
// 	p.routingMu.RLock()
// 	defer p.routingMu.RUnlock()
// 	out := make([]string, 0, 1)
// 	for _, router := range p.routing {
// 		choices := make([]randutil.Choice, 0, len(router))
// 		for prob, urls := range router {
// 			prob, _ := strconv.Atoi(prob)
// 			choice := randutil.Choice{
// 				Weight: int(prob),
// 				Item:   urls,
// 			}
// 			choices = append(choices, choice)
// 		}
// 		result, _ := randutil.WeightedChoice(choices)
// 		var _, _ = result.Item.([]string)
// 	}
// 	return out
// }
