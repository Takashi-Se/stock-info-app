new Vue({
    el: '#app',
    data: {
        code: '',
        stock: null,
        favorites: { tabs: [{ name: 'お気に入り', stocks: [] }] },
        currentTabIndex: 0,
        sortBy: 'code',
        editMode: false,
        status: '準備完了'
    },
    computed: {
        currentTabStocks() {
            if (this.favorites.tabs && this.favorites.tabs.length > 0) {
                return this.favorites.tabs[this.currentTabIndex].stocks;
            }
            return [];
        }
    },
    mounted() {
        // お気に入り情報を読み込む
        this.loadFavorites();
    },
    methods: {
        // 株価検索
        async searchStock() {
            if (!this.code || !/^\d{4}$/.test(this.code)) {
                alert('証券コードは4桁の数字で入力してください。');
                return;
            }

            this.status = `証券コード ${this.code} の情報を取得中...`;

            try {
                const response = await axios.get(`/api/search?code=${this.code}`);
                if (response.data.error) {
                    alert(response.data.error);
                    this.status = '情報の取得に失敗しました';
                    return;
                }

                this.stock = response.data;
                this.status = '情報を取得しました';
            } catch (error) {
                console.error('検索エラー:', error);
                alert('株価情報の取得に失敗しました。');
                this.status = '情報の取得に失敗しました';
            }
        },

        // お気に入りに追加
        async addToFavorites() {
            if (!this.stock) return;

            try {
                const response = await axios.post('/api/favorites', {
                    tab_index: this.currentTabIndex,
                    stock: this.stock
                });

                if (response.data.error) {
                    alert(response.data.error);
                    return;
                }

                this.loadFavorites();
                this.status = `${this.stock.name} をお気に入りに追加しました`;
            } catch (error) {
                console.error('お気に入り追加エラー:', error);
                alert('お気に入りの追加に失敗しました。');
            }
        },

        // お気に入りから削除
        async removeFromFavorites(code) {
            if (!confirm('この銘柄をお気に入りから削除しますか？')) return;

            try {
                const response = await axios.post('/api/favorites/remove', {
                    tab_index: this.currentTabIndex,
                    code: code
                });

                if (response.data.error) {
                    alert(response.data.error);
                    return;
                }

                this.loadFavorites();
                this.status = 'お気に入りから削除しました';
            } catch (error) {
                console.error('お気に入り削除エラー:', error);
                alert('お気に入りの削除に失敗しました。');
            }
        },

        // お気に入り情報を読み込む
        async loadFavorites() {
            try {
                const response = await axios.get('/api/favorites');
                this.favorites = response.data;
            } catch (error) {
                console.error('お気に入り読み込みエラー:', error);
            }
        },

        // タブを追加
        async addTab() {
            const name = prompt('新しいタブ名を入力してください:');
            if (!name) return;

            try {
                const response = await axios.post('/api/favorites/tab', { name });
                if (response.data.error) {
                    alert(response.data.error);
                    return;
                }

                this.loadFavorites();
                // 新しいタブを選択
                this.currentTabIndex = this.favorites.tabs.length - 1;
            } catch (error) {
                console.error('タブ追加エラー:', error);
                alert('タブの追加に失敗しました。');
            }
        },

        // 株価情報を並べ替え
        sortStocks() {
            if (!this.favorites.tabs || !this.favorites.tabs[this.currentTabIndex]) return;

            const stocks = this.favorites.tabs[this.currentTabIndex].stocks;
            
            if (this.sortBy === 'code') {
                stocks.sort((a, b) => a.code.localeCompare(b.code));
            } else if (this.sortBy === 'name') {
                stocks.sort((a, b) => a.name.localeCompare(b.name));
            } else if (this.sortBy === 'price') {
                stocks.sort((a, b) => b.current_price - a.current_price);
            } else if (this.sortBy === 'diff') {
                stocks.sort((a, b) => b.prev_diff_percent - a.prev_diff_percent);
            }
            // 'custom'の場合は何もしない

            // 変更をサーバーに保存
            this.saveFavorites();
        },

        // お気に入り情報を保存
        async saveFavorites() {
            try {
                await axios.post('/api/favorites', {
                    tab_index: this.currentTabIndex,
                    favorites: this.favorites
                });
            } catch (error) {
                console.error('お気に入り保存エラー:', error);
            }
        },

        // 株価の前日比のクラスを取得
        getDiffClass(diff) {
            if (diff > 0) return 'up';
            if (diff < 0) return 'down';
            return '';
        },

        // 現在の株価の外部サイトのURLを取得
        getStockUrl(site) {
            if (!this.stock) return '#';
            
            if (site === 'kabutan') {
                return `https://kabutan.jp/stock/?code=${this.stock.code}`;
            } else if (site === 'minkabu') {
                return `https://minkabu.jp/stock/${this.stock.code}`;
            } else if (site === 'yahoo') {
                return `https://finance.yahoo.co.jp/quote/${this.stock.code}.T`;
            }
            return '#';
        },

        // お気に入りの銘柄の外部サイトのURLを取得
        getExternalUrl(code, site) {
            if (site === 'kabutan') {
                return `https://kabutan.jp/stock/?code=${code}`;
            } else if (site === 'minkabu') {
                return `https://minkabu.jp/stock/${code}`;
            } else if (site === 'yahoo') {
                return `https://finance.yahoo.co.jp/quote/${code}.T`;
            }
            return '#';
        },

        // 数値のフォーマット（価格）
        formatPrice(price) {
            return price ? price.toLocaleString() : '0';
        },

        // 数値のフォーマット（前日比）
        formatDiff(diff) {
            const prefix = diff > 0 ? '▲' : diff < 0 ? '▼' : '';
            return `${prefix}${Math.abs(diff).toLocaleString()}`;
        },

        // 数値のフォーマット（パーセント）
        formatPercent(percent) {
            return percent ? percent.toFixed(2) : '0.00';
        }
    }
});
