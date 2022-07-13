package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"net/http"
	"net/http/httputil"
	"net/url"
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

func (p *ProxyRouter) GetHost() string {
	p.routingMu.RLock()
	defer p.routingMu.RUnlock()
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
		urls, _ := result.Item.([]string)
		url_choices := make([]randutil.Choice, 0, len(urls))
		for _, url := range urls {
			choice := randutil.Choice{
				Weight: int(100 / len(urls)),
				Item:   url,
			}
			url_choices = append(url_choices, choice)
		}
		result, _ = randutil.WeightedChoice(url_choices)
		selected_url, _ := result.Item.(string)
		return selected_url
	}
	return "Error"
}

func handlerReverseProxy(p *httputil.ReverseProxy) func(http.ResponseWriter, *http.Request) {
	return func(w http.ResponseWriter, r *http.Request) {
		p.ServeHTTP(w, r)
	}
}

func main() {
	host := flag.String("host", "0.0.0.0", "Address of the server")
	port := flag.String("port", "8000", "Port of the server")
	flag.Parse()

	proxyRouter := &ProxyRouter{
		routingMu: &sync.RWMutex{},
	}
	reverseProxy := &httputil.ReverseProxy{}

	reverseProxy.Director = func(r *http.Request) {
		url, _ := url.Parse(proxyRouter.GetHost())
		r.URL.Scheme = url.Scheme
		r.URL.Host = url.Host
	}

	// https://github.com/gorilla/mux
	r := mux.NewRouter()
	r.HandleFunc("/api/v1/proxy", func(w http.ResponseWriter, r *http.Request) {
		decoder := json.NewDecoder(r.Body)
		proxyRouter.UpdateRouting(decoder)
	})

	r.PathPrefix("/").HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/" {
			json.NewEncoder(w).Encode(map[string]string{"status": "Ready"})
		} else {
			if len(proxyRouter.routing) == 0 {
				json.NewEncoder(w).Encode(map[string]string{"status": "Not Ready"})
			} else {
				reverseProxy.ServeHTTP(w, r)
			}
		}
	})

	srv := &http.Server{
		Handler: r,
		Addr:    fmt.Sprintf("%s:%s", *host, *port),
		// Good practice: enforce timeouts for servers you create
		WriteTimeout: 15 * time.Second,
		ReadTimeout:  15 * time.Second,
	}

	_ = srv.ListenAndServe()
}
