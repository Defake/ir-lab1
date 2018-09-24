(ns spell-checker.core
  (:require [spell-checker.levs :as lev]
            [monger.core :as mg]
            [monger.collection :as mc]
            [clojure.string :as str]))

(def conn (mg/connect))
(def db (mg/get-db conn "ir_lab_texts"))
(def news-coll "news_texts")
(def tokens-coll "corpus_tokens")
(def tgrams-coll "tgrams_tokens")

(defn into-tgrams [word]
  (loop [token (seq (str "__" word "__"))
         grams []]
    (if (<= 3 (count token))
      (recur (rest token)
             (conj grams (apply str (take 3 token))))
      grams)))

(defn get-words-map [texts]
  (->> texts
       (map #(re-seq #"\p{L}+" %))
       (flatten)
       (filter identity)
       (map #(str/lower-case %))
       (reduce #(merge-with + %1 {%2 1}) {})))

(defn update-tgrams-base [base [word tgrams]]
  (reduce
    (fn [base tgram]
      (if (get base tgram)
        (update-in base [tgram] #(conj % word))
        (assoc base tgram #{word})))
    base
    tgrams))

(def words-base
  (->> (mc/find-maps db news-coll)
       ;(take 1000)
       (map :text)
       (get-words-map)))

(def tgrams-base
  (->> (keys words-base)
       (map #(vector % (into-tgrams %)))
       (reduce #(update-tgrams-base %1 %2) {})))

;; Db

(defn define-tgrams-coll
  "Inserting to tgrams collection such structures:
  {:_id #object[org.bson.types.ObjectId],
   :tgram вза,
   :words [взаимоотношений, взаимозависимым, взаимодополняемости, взаимными, ...]"
  [base]
  (doseq [[tgram words] base]
    (mc/insert-and-return db tgrams-coll {:tgram tgram
                                          :words words})))

(defn define-words-coll
  "Inserting to db structures:
   {:_id #object[org.bson.types.ObjectId],
    :word мышкой,
    :amount 9},
   {:_id #object[org.bson.types.ObjectId]
    :word горлового,
    :amount 3}"
  [base]
  (doseq [[word amount] base]
    (mc/insert-and-return db tokens-coll {:word word
                                          :amount amount})))

;(define-tgrams-coll tgrams-base)
;(define-words-coll words-base)
;(mc/create-index db tgrams-coll (array-map :tgram 1))
;(mc/create-index db tokens-coll (array-map :word 1))


;; Fixing

(defn fix-typo [word n]
  (let [tgrams (into-tgrams word)
        sorted-tokens (->> tgrams
                           (map #(:words (mc/find-one-as-map db tgrams-coll {:tgram %})))
                           (flatten)
                           (set)
                           (map #(vector % (lev/lev word %)))
                           (sort-by #(get % 1)))]
    (->> (take n sorted-tokens)
         (map #(conj % (:amount (mc/find-one-as-map db tokens-coll {:word (get % 0)}))))
         (sort-by (juxt #(get % 1) #(/ 1 (get % 2)))))))

(time
  (fix-typo "транспот" 15))
;; "Elapsed time: 18479.080019 msecs"
;; =>
;(["транспорт" 1 133
; ["транспорта" 2 365]
; ["транспорте" 2 123]
; ["транспорту" 2 9]
; ["транспорты" 2 6]
; ["трансп" 2 1]
; ["иранской" 3 69]
; ["иранское" 3 15]
; ["трампов" 3 5]
; ["транспортер" 3 4]
; ["иранско" 3 3]
; ["транслейт" 3 1]
; ["трампо" 3 1]
; ["транса" 3 1]
; ["трансгаз" 3 1]])


(time
  (fix-typo "порграмма" 10))
;; "Elapsed time: 53419.221831 msecs"
;; =>
;(["программа" 1 709
; ["программы" 2 1322]
; ["программу" 2 631]
; ["программе" 2 569]
; ["программ" 2 305]
; ["программах" 2 50]
; ["программам" 2 43]
; ["погрома" 3 10]
; ["эпиграмма" 3 3]
; ["поиграла" 3 1]])

(time
  (fix-typo "приевт" 20))
;; "Elapsed time: 28235.124484 msecs"
;; =>
;(["привет" 1 102
; ["принят" 2 391]
; ["примут" 2 279]
; ["привел" 2 248]
; ["примет" 2 243]
; ["приема" 2 170]
; ["придут" 2 115]
; ["приедет" 2 88]
; ["приедут" 2 58]
; ["приют" 2 49]
; ["приему" 2 33]
; ["придёт" 2 20]
; ["приветы" 2 5]
; ["прив" 2 2]
; ["ориент" 2 1]
; ["призва" 2 1]
; ["привит" 2 1]
; ["прит" 2 1]
; ["приветъ" 2 1]
; ["прист" 2 1]])

(time
  (fix-typo "превед" 20))
;; "Elapsed time: 24557.161215 msecs"
;; =>
;(["перед" 2 3299
; ["прежде" 2 1530]
; ["провел" 2 508]
; ["привел" 2 248]
; ["перевел" 2 45]
; ["пред" 2 41]
; ["приведу" 2 31]
; ["перевес" 2 25]
; ["переведя" 2 13]
; ["правее" 2 10]
; ["приведи" 2 9]
; ["пресек" 2 6]
; ["проведу" 2 5]
; ["первее" 2 3]
; ["препод" 2 2]
; ["провез" 2 2]
; ["прервет" 2 2]
; ["председ" 2 1]
; ["реве" 2 1]
; ["ревел" 2 1]])
